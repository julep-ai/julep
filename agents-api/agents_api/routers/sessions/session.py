import json
from functools import reduce
from json import JSONDecodeError
from typing import Callable
from uuid import uuid4
from openai.types.chat.chat_completion import ChatCompletion
from dataclasses import dataclass
from pydantic import UUID4
from agents_api.clients.embed import embed
from agents_api.env import summarization_tokens_threshold
from agents_api.clients.temporal import run_summarization_task
from agents_api.models.entry.add_entries import add_entries_query
from agents_api.common.protocol.entries import Entry
from agents_api.common.exceptions.sessions import SessionNotFoundError
from agents_api.clients.worker.types import ChatML
from agents_api.models.session.session_data import get_session_data
from agents_api.models.entry.proc_mem_context import proc_mem_context_query
from agents_api.autogen.openapi_model import InputChatMLMessage, Tool
from agents_api.model_registry import (
    get_extra_settings,
    get_model_client,
    load_context,
)
from ...common.protocol.sessions import SessionData
from .protocol import Settings
from .exceptions import InputTooBigError


THOUGHTS_STRIP_LEN = 2
MESSAGES_STRIP_LEN = 4


tool_query_instruction = (
    "Transform this user request for fetching helpful tool descriptions: "
)
instruction_query_instruction = (
    "Embed this text chunk for finding useful historical chunks: "
)
doc_query_instruction = (
    "Encode this query and context for searching relevant passages: "
)


@dataclass
class BaseSession:
    session_id: UUID4
    developer_id: UUID4

    def _remove_messages(
        self,
        messages: list[Entry],
        start_idx: int | None,
        end_idx: int | None,
        token_count: int,
        summarization_tokens_threshold: int,
        predicate: Callable[[Entry], bool],
    ) -> tuple[list[Entry], int]:
        if len(messages) < abs((end_idx or len(messages)) - (start_idx or 0)):
            return messages, token_count

        result: list[Entry] = messages[: start_idx or 0]
        skip_check = False
        for m in messages[start_idx:end_idx]:
            if predicate(m) and not skip_check:
                token_count -= m.token_count
                if token_count <= summarization_tokens_threshold:
                    skip_check = True

                continue

            result.append(m)

        if end_idx is not None:
            result += messages[end_idx:]

        return result, token_count

    def truncate(
        self, messages: list[Entry], summarization_tokens_threshold: int
    ) -> list[Entry]:
        def rm_thoughts(m):
            return m.role == "system" and m.name == "thought"

        def rm_user_assistant(m):
            return m.role in ("user", "assistant")

        token_count = reduce(lambda c, e: e.token_count + c, messages, 0)

        if token_count <= summarization_tokens_threshold:
            return messages

        for start_idx, end_idx, cond in [
            (THOUGHTS_STRIP_LEN, -THOUGHTS_STRIP_LEN, rm_thoughts),
            (None, None, rm_thoughts),
            (MESSAGES_STRIP_LEN, -MESSAGES_STRIP_LEN, rm_user_assistant),
        ]:
            messages, token_count = self._remove_messages(
                messages,
                start_idx,
                end_idx,
                token_count,
                summarization_tokens_threshold,
                cond,
            )

            if token_count <= summarization_tokens_threshold and messages:
                return messages

        # TODO:
        # Compress info sections using LLM Lingua
        #   - If more space is still needed, remove info sections iteratively

        raise InputTooBigError(token_count, summarization_tokens_threshold)

    async def run(
        self, new_input, settings: Settings
    ) -> tuple[ChatCompletion, Entry, Callable]:
        # TODO: implement locking at some point
        # Get session data
        session_data = get_session_data(self.developer_id, self.session_id)
        if session_data is None:
            raise SessionNotFoundError(self.developer_id, self.session_id)
        # Assemble context
        init_context, final_settings = await self.forward(
            session_data, new_input, settings
        )
        # Generate response
        response = await self.generate(
            self.truncate(init_context, summarization_tokens_threshold), final_settings
        )
        # Save response to session
        # if final_settings.get("remember"):
        #     await self.add_to_session(new_input, response)

        message = response.choices[0].message
        role = message.role
        content = message.content

        # Unpack tool calls if present
        # TODO: implement changes in the openapi spec
        # Currently our function_call does the same job as openai's function role
        # Need to add a new role for openai's paradigm of shoving function selected into assistant's context
        # Ref: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_call_functions_with_chat_models.ipynb
        if not message.content and message.tool_calls:
            role = "function_call"
            function_call = message.tool_calls[0].function.model_dump()
            content = json.dumps(function_call)
            # FIXME: what?? why is this happening?? could be a bug in the model api
            # this is only a hack for samantha-1-turbo
            # content = content[content.index("{", 1) :]
        elif not message.content:
            raise ValueError("No content in response")

        total_tokens = response.usage.total_tokens
        completion_tokens = response.usage.completion_tokens
        new_entry = Entry(
            session_id=self.session_id,
            role=role,
            name=None if session_data is None else session_data.agent_name,
            content=content,
            token_count=completion_tokens,
        )
        # Return response and the backward pass as a background task (dont await here)
        backward_pass = await self.backward(
            new_input, total_tokens, new_entry, final_settings
        )

        return response, new_entry, backward_pass

    async def forward(
        self,
        session_data: SessionData | None,
        new_input: list[Entry],
        settings: Settings,
    ) -> tuple[list[ChatML], Settings]:
        # role, name, content, token_count, created_at
        string_to_embed = "\n".join(
            [f"{msg.name or msg.role}: {msg.content}" for msg in new_input]
        )

        (
            tool_query_embedding,
            doc_query_embedding,
        ) = await embed(
            [
                instruction + string_to_embed
                for instruction in [
                    tool_query_instruction,
                    doc_query_instruction,
                ]
            ],
            join_inputs=False,
        )

        entries: list[Entry] = []
        instructions = "IMPORTANT INSTRUCTIONS:\n\n"
        first_instruction_idx = -1
        first_instruction_created_at = 0
        tools = []
        for idx, row in proc_mem_context_query(
            session_id=self.session_id,
            tool_query_embedding=tool_query_embedding,
            doc_query_embedding=doc_query_embedding,
        ).iterrows():
            # If a `functions` message is encountered, extract into tools list
            if row["name"] == "functions":
                # FIXME: This might also break if {role: system, name: functions, content} but content not valid json object
                try:
                    saved_function = json.loads(row["content"])
                except JSONDecodeError as e:
                    # FIXME: raise a proper error that can be caught by the router
                    raise ValueError(str(e))

                tool = Tool(type="function", function=saved_function, id=str(uuid4()))
                tools.append(tool)

                continue

            # If `instruction` encoountered, extract and compile together (because of a quirk in how cozo queries work)
            if row["name"] == "instruction":
                if first_instruction_idx < 0:
                    first_instruction_idx = idx
                    first_instruction_created_at = row["created_at"]

                instructions += f"- {row['content']}\n"

                continue

            # Else add to entries as is
            entries.append(
                Entry(
                    **{
                        "role": row["role"],
                        "name": row["name"],
                        "content": row["content"],
                        "session_id": self.session_id,
                        "created_at": row["created_at"],
                    }
                )
            )

        # If any instructions were found, add them as info block
        if first_instruction_idx >= 0:
            entries.insert(
                first_instruction_idx,
                Entry(
                    role="system",
                    name="information",
                    content=instructions,
                    session_id=self.session_id,
                    created_at=first_instruction_created_at,
                ),
            )

        messages = [
            ChatML(
                role=e.role.value if hasattr(e.role, "value") else e.role,
                name=e.name,
                content=(
                    e.content
                    if not isinstance(e.content, list)
                    else "\n".join(e.content)
                ),
            )
            for e in entries + new_input
            if e.content
        ]

        # FIXME: This sometimes returns "The model `` does not exist."
        if session_data is not None:
            settings.model = session_data.model

        # Add tools to settings
        if tools:
            settings.tools = settings.tools or []
            settings.tools.extend(tools)

        return messages, settings

    async def generate(
        self, init_context: list[ChatML], settings: Settings
    ) -> ChatCompletion:
        init_context = load_context(init_context, settings.model)
        tools = None
        if settings.tools:
            tools = [(tool.model_dump(exclude="id")) for tool in settings.tools]
        model_client = get_model_client(settings.model)
        extra_body = get_extra_settings(settings)

        res = await model_client.chat.completions.create(
            model=settings.model,
            messages=init_context,
            max_tokens=settings.max_tokens,
            stop=settings.stop,
            temperature=settings.temperature,
            frequency_penalty=settings.frequency_penalty,
            extra_body=extra_body,
            top_p=settings.top_p,
            presence_penalty=settings.presence_penalty,
            stream=settings.stream,
            tools=tools,
            response_format=settings.response_format,
        )
        return res

    async def backward(
        self,
        new_input: list[InputChatMLMessage],
        total_tokens: int,
        new_entry: Entry,
        final_settings: Settings,
    ) -> Callable | None:
        if not final_settings.remember:
            return

        entries: list[Entry] = []
        for m in new_input:
            entries.append(
                Entry(
                    session_id=self.session_id,
                    role=m.role,
                    content=m.content,
                    name=m.name,
                )
            )

        entries.append(new_entry)
        add_entries_query(entries)

        if total_tokens >= summarization_tokens_threshold:
            return run_summarization_task


class PlainCompletionSession(BaseSession):
    pass


class RecursiveSummarizationSession(PlainCompletionSession):
    pass
