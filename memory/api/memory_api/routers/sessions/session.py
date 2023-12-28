from typing import Tuple, Callable
import openai
from dataclasses import dataclass
from pydantic import UUID4
from memory_api.clients.cozo import client
from memory_api.models.entry.add_entries import add_entries_query
from memory_api.common.protocol.entries import Entry
from memory_api.clients.worker.types import ChatML
from memory_api.models.entry.naive_context_window import naive_context_window_query
from memory_api.models.session.session_data import get_session_data
from .protocol import Settings


@dataclass
class BaseSession:
    session_id: UUID4

    async def run(self, new_input, settings) -> Tuple[ChatML, Callable]:
        # TODO: implement locking at some point

        # Get session data
        session_data = get_session_data(self.session_id)

        # Assemble context
        init_context, final_settings = await self.forward(
            session_data, new_input, settings
        )

        # Generate response
        response = await self.generate(init_context, final_settings)

        # Save response to session
        # if final_settings.get("remember"):
        #     await self.add_to_session(new_input, response)

        # Return response and the backward pass as a background task (dont await here)
        backward_pass = self.backward(session_data, new_input, response, final_settings)

        return response, backward_pass

    async def forward(
        self, session_data, new_input: list[Entry], settings
    ) -> Tuple[ChatML, Settings]:
        # role, name, content, token_count, created_at
        entries = [
            {
                "role": row["role"],
                "name": row["name"],
                "content": row["content"],
            } 
            for _, row in client.run(
                naive_context_window_query(self.session_id),
            ).iterrows()
        ]

        messages = [
            {
                "role": e.role,
                "name": e.name,
                "content": e.content
                if not isinstance(e.content, list)
                else "\n".join(e.content),
            }
            for e in new_input + entries
            if e.content
        ]

        return messages, settings

    async def generate(self, init_context, settings: Settings) -> ChatML:
        # TODO: how to use response_format ?
        
        return openai.ChatCompletion.create(
            model=settings.model,
            messages=init_context,
            max_tokens=settings.max_tokens,
            stop=settings.stop,
            temperature=settings.temperature,
            frequency_penalty=settings.frequency_penalty,
            repetition_penalty=settings.repetition_penalty,
            best_of=1,
            top_p=settings.top_p,
            top_k=1,
            length_penalty=settings.length_penalty,
            # logit_bias=settings.logit_bias,
            presence_penalty=settings.presence_penalty,
            stream=settings.stream,
        )

    async def backward(self, session_data, new_input, response, final_settings) -> None:
        entries: list[Entry] = []
        for m in new_input:
            m.session_id = self.session_id
            entries.append(m)

        entries.append(
            Entry(
                session_id=self.session_id,
                role="assistant",
                name=final_settings["name"],
                content=response["choices"][0]["text"],
                token_count=response["usage"]["total_tokens"],
            )
        )
        client.run(add_entries_query(entries))


class PlainCompletionSession(BaseSession):
    pass


class RecursiveSummarizationSession(PlainCompletionSession):
    async def _query_summary_messages(self) -> ChatML:
        """Get messages leaf nodes on summary tree from cozo"""
        ...

    async def forward(
        self, session_data, new_input, settings
    ) -> Tuple[ChatML, Settings]:
        # Don't call super: we dont want normal messages anyway

        # Settings dont change
        final_settings = {**settings}

        context = await self._query_summary_messages()
        return context, final_settings

    async def backward(self, session_data, new_input, response) -> None:
        pass
