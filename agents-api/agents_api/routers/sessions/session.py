import json
import xxhash
from functools import reduce
from json import JSONDecodeError
from typing import Callable
from uuid import uuid4
from functools import partial

from dataclasses import dataclass
from openai.types.chat.chat_completion import ChatCompletion
from pydantic import UUID4

import litellm
from litellm import acompletion

from ...autogen.openapi_model import InputChatMLMessage, Tool, DocIds
from ...clients.embed import embed
from ...clients.temporal import run_summarization_task
from ...clients.temporal import run_truncation_task
from ...clients.worker.types import ChatML
from ...common.exceptions.sessions import SessionNotFoundError
from ...common.protocol.entries import Entry
from ...common.protocol.sessions import SessionData
from ...common.utils.template import render_template
from ...common.utils.json import CustomJSONEncoder
from ...common.utils.messages import stringify_content
from ...env import (
    embedding_service_url,
    embedding_model_id,
)
from ...model_registry import (
    LOCAL_MODELS,
    LOCAL_MODELS_WITH_TOOL_CALLS,
    load_context,
    validate_and_extract_tool_calls,
)
from ...models.entry.add_entries import add_entries_query
from ...models.entry.proc_mem_context import proc_mem_context_query
from ...models.session.session_data import get_session_data
from ...models.session.get_cached_response import get_cached_response
from ...models.session.set_cached_response import set_cached_response
from ...exceptions import PromptTooBigError

from .exceptions import InputTooBigError
from .protocol import Settings
from ...env import model_inference_url, model_api_key

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


def cache(f):
    async def wrapper(
        self, init_context: list[ChatML], settings: Settings
    ) -> ChatCompletion:
        key = xxhash.xxh64(
            json.dumps(
                {
                    "init_context": [c.model_dump() for c in init_context],
                    "settings": settings.model_dump(),
                },
                cls=CustomJSONEncoder,
                default_empty_value="",
            )
        ).hexdigest()
        result = get_cached_response(key=key)
        if not result.size:
            resp = await f(self, init_context, settings)
            set_cached_response(key=key, value=resp.model_dump())
            return resp
        choices = result.iloc[0].to_dict()["value"]
        return ChatCompletion(**choices)

    return wrapper


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

    def _truncate_context(
        self, messages: list[Entry], summarization_tokens_threshold: int | None
    ) -> list[Entry]:
        def rm_thoughts(m):
            return m.role == "system" and m.name == "thought"

        def rm_user_assistant(m):
            return m.role in ("user", "assistant")

        if summarization_tokens_threshold is None:
            return messages

        token_count = reduce(lambda c, e: (e.token_count or 0) + c, messages, 0)

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
    ) -> tuple[ChatCompletion, Entry, Callable | None, DocIds]:
        # TODO: implement locking at some point

        # Get session data
        session_data = get_session_data(self.developer_id, self.session_id)
        if session_data is None:
            raise SessionNotFoundError(self.developer_id, self.session_id)

        # Assemble context
        init_context, final_settings, doc_ids = await self.forward(
            session_data, new_input, settings
        )

        # Generate response
        response = await self.generate(
            self._truncate_context(init_context, final_settings.token_budget),
            final_settings,
        )

        # Save response to session
        # if final_settings.get("remember"):
        #     await self.add_to_session(new_input, response)

        # FIXME: Implement support for multiple choices, will need a revisit to the schema
        message = response.choices[0].message
        role = message.role
        content = message.content

        # FIXME: Implement support for multiple tool calls

        # Unpack tool calls if present
        # TODO: implement changes in the openapi spec
        # Currently our function_call does the same job as openai's function role
        # Need to add a new role for openai's paradigm of shoving function selected into assistant's context
        # Ref: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_call_functions_with_chat_models.ipynb
        if not message.content and message.tool_calls:
            role = "function_call"
            content = message.tool_calls[0].function.model_dump_json()

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

        return response, new_entry, backward_pass, doc_ids

    async def forward(
        self,
        session_data: SessionData | None,
        new_input: list[Entry],
        settings: Settings,
    ) -> tuple[list[ChatML], Settings, DocIds]:
        if session_data is not None:
            settings.token_budget = session_data.token_budget
            settings.context_overflow = session_data.context_overflow

        stringified_input = []
        for msg in new_input:
            stringified_input.append(
                (
                    msg.role,
                    msg.name,
                    stringify_content(msg.content),
                )
            )

        # role, name, content, token_count, created_at
        string_to_embed = "\n".join(
            [
                f"{name or role}: {content}"
                for (role, name, content) in stringified_input
                if content
            ]
        )

        # FIXME: bge-m3 does not require instructions
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
            embedding_service_url=embedding_service_url,
            embedding_model_name=embedding_model_id,
        )

        entries: list[Entry] = []
        instructions = "Instructions:\n\n"
        first_instruction_idx = -1
        first_instruction_created_at = 0
        tools = []
        doc_ids = DocIds(agent_doc_ids=[], user_doc_ids=[])

        for idx, row in proc_mem_context_query(
            session_id=self.session_id,
            tool_query_embedding=tool_query_embedding,
            doc_query_embedding=doc_query_embedding,
        ).iterrows():
            agent_doc_id = row.get("agent_doc_id")
            user_doc_id = row.get("user_doc_id")

            if agent_doc_id is not None:
                doc_ids.agent_doc_ids.append(agent_doc_id)

            if user_doc_id is not None:
                doc_ids.user_doc_ids.append(user_doc_id)

            # If a `functions` message is encountered, extract into tools list
            if row["name"] == "functions":
                # FIXME: This might also break if {role: system, name: functions, content} but content not valid json object
                try:
                    # FIXME: This is a hack for now, need to fix to support multiple function calls
                    assert (
                        len(row["content"]) == 1
                    ), "Only one function can be called at a time"
                    content = row["content"][0]["text"]
                    saved_function = json.loads(content)
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

                instructions += f"{row['content'][0]['text']}" + "\n\n"

                continue

            # Else add to entries as is
            entries.append(
                Entry(
                    role=row["role"],
                    name=row["name"],
                    content=row["content"],
                    session_id=self.session_id,
                    created_at=row["created_at"],
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
                content=e.content,
            )
            for e in entries + new_input
            if e.content
        ]

        # Simplify messages if possible
        for message in messages:
            if (
                isinstance(message.content, list)
                and len(message.content) == 1
                and message.content[0].type == "text"
            ):
                message.content = message.content[0].text
                # Add tools to settings
        if tools:
            settings.tools = settings.tools or []
            settings.tools.extend(tools)
        # If render_templates=True, render the templates
        if session_data is not None and session_data.render_templates:

            template_data = {
                "session": {
                    "id": session_data.session_id,
                    "situation": session_data.situation,
                    "metadata": session_data.metadata,
                },
                "user": {
                    "id": session_data.user_id,
                    "name": session_data.user_name,
                    "about": session_data.user_about,
                    "metadata": session_data.user_metadata,
                },
                "agent": {
                    "id": session_data.agent_id,
                    "name": session_data.agent_name,
                    "about": session_data.agent_about,
                    "metadata": session_data.agent_metadata,
                    "tools": settings.tools,
                },
            }

            for i, msg in enumerate(messages):
                # Only render templates for system/assistant messages
                if msg.role not in ["system", "assistant"]:
                    continue

                messages[i].content = await render_template(msg.content, template_data)

        # FIXME: This sometimes returns "The model `` does not exist."
        if session_data is not None:
            settings.model = session_data.model

        return messages, settings, doc_ids

    @cache
    async def generate(
        self, init_context: list[ChatML], settings: Settings
    ) -> ChatCompletion:
        init_context = load_context(init_context, settings.model)
        tools = None
        api_base = None
        api_key = None
        model = settings.model
        if model in LOCAL_MODELS:
            api_base = model_inference_url
            api_key = model_api_key
            model = f"openai/{model}"

        if settings.tools:
            tools = [(tool.model_dump(exclude="id")) for tool in settings.tools]

        litellm.drop_params = True
        litellm.add_function_to_prompt = True
        res = await acompletion(
            model=model,
            messages=init_context,
            max_tokens=settings.max_tokens,
            stop=settings.stop,
            temperature=settings.temperature,
            frequency_penalty=settings.frequency_penalty,
            top_p=settings.top_p,
            presence_penalty=settings.presence_penalty,
            stream=settings.stream,
            tools=tools,
            response_format=settings.response_format,
            api_base=api_base,
            api_key=api_key,
        )
        if model in LOCAL_MODELS_WITH_TOOL_CALLS:
            validation, tool_call, error_msg = validate_and_extract_tool_calls(
                res.choices[0].message.content
            )
            if validation:
                res.choices[0].message.role = (
                    "function_call" if tool_call else "assistant"
                )
                res.choices[0].finish_reason = "tool_calls"
                res.choices[0].message.tool_calls = tool_call
                res.choices[0].message.content = json.dumps(tool_call)
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
        bg_task = None

        if (
            final_settings.token_budget is not None
            and total_tokens >= final_settings.token_budget
        ):
            if final_settings.context_overflow == "truncate":
                bg_task = partial(run_truncation_task, final_settings.token_budget)
            elif final_settings.context_overflow == "adaptive":
                bg_task = run_summarization_task
            else:
                raise PromptTooBigError(total_tokens, final_settings.token_budget)

        add_entries_query(entries)

        return bg_task


class PlainCompletionSession(BaseSession):
    pass


class RecursiveSummarizationSession(PlainCompletionSession):
    pass
