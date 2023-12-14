from typing import Tuple
import uuid
import openai
from dataclasses import dataclass
from operator import itemgetter
from fastapi import HTTPException, status
from pydantic import UUID4
from memory_api.clients.cozo import client
from memory_api.common.db.entries import add_entries
from memory_api.common.protocol.entries import Entry
from memory_api.env import summarization_ratio_threshold
from memory_api.clients.worker.types import MemoryManagementTaskArgs, ChatML
from memory_api.clients.worker.worker import add_summarization_task
from .queries import context_window_query_beliefs


models_map = {
    "samantha-1-alpha": "julep-ai/samantha-1-alpha",
}


@dataclass
class BaseSession:
    session_id: UUID4

    async def get_session_data(self):
        pass

    async def run(self, new_input, settings) -> Tuple[Response, BackgroundTask]:
        # TODO: implement locking at some point

        # Get session data
        session_data = await self.get_session_data()

        # Assemble context
        init_context, final_settings = await self.forward(session_data, new_input, settings)

        # Generate response
        response = await self.generate(init_context, final_settings)

        # Save response to session
        if final_settings.get("remember"):
            await self.add_to_session(new_input, response)

        # Return response and the backward pass as a background task (dont await here)
        backward_pass = self.backward(session_data, new_input, response, final_settings)

        return response, backward_pass

  
    async def forward(self, session_data, new_input, settings) -> Tuple[ChatML, Settings]:
        entries: list[Entry] = []
        for m in new_input:
            m.session_id = self.session_id
            entries.append(m)
        
        add_entries(entries)

        resp = client.run(context_window_query_beliefs.replace("{session_id}", self.session_id))

        try:
            model_data = resp["model_data"][0]
            agent_data = resp["character_data"][0]
        except (IndexError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Character or model data not found",
            )
        
        entries = sorted(resp["entries"][0], key=itemgetter("timestamp"))
        summarization_threshold = model_data["max_length"] * summarization_ratio_threshold

        if resp["total_tokens"][0] >= summarization_threshold:
            await add_summarization_task(
                MemoryManagementTaskArgs(
                    session_id=self.session_id, 
                    model=models_map.get(model_data["model_name"], model_data["model_name"]), 
                    dialog=[
                        ChatML(
                            **{
                                **e, 
                                "session_id": self.session_id, 
                                "entry_id": uuid.UUID(bytes=bytes(e.get("entry_id"))),
                            },
                        ) 
                        for e in entries if e.get("role") != "system"
                    ],
                ),
            )

        # generate response
        default_settings = model_data["default_settings"]
        messages = [
            {
                "role": e.get("role"), 
                "name": e.get("name"), 
                "content": e["content"] if not isinstance(e["content"], list) else "\n".join(e["content"]),
            } 
            for e in entries if e.get("content")
        ]

        return messages, default_settings

    async def generate(self, init_context, final_settings) -> ChatML:
        response = openai.ChatCompletion.create(
            model=final_settings["model_name"],
            messages=init_context,
            max_tokens=final_settings["max_tokens"],
            temperature=final_settings["temperature"],
            repetition_penalty=final_settings["repetition_penalty"],
            frequency_penalty=final_settings["frequency_penalty"],
        )

        # add response as an entry
        add_entries(
            [
                Entry(
                    session_id=self.session_id, 
                    role="assistant", 
                    name=final_settings["name"], 
                    content=response["choices"][0]["text"], 
                    token_count=response["usage"]["total_tokens"],
                )
            ]
        )

    async def backward(self, session_data, new_input, response, final_settings) -> None:
        pass


class PlainCompletionSession(BaseSession):
    pass


class RecursiveSummarizationSession(PlainCompletionSession):
    async def _query_summary_messages(self) -> ChatML:
        """Get messages leaf nodes on summary tree from cozo"""
        ...
    
    async def forward(self, session_data, new_input, settings) -> Tuple[ChatML, Settings]:
        # Don't call super: we dont want normal messages anyway

        # Settings dont change
        final_settings = {**settings}

        context = await self._query_summary_messages()
        return context, final_settings
  
    async def backward(self, session_data, new_input, response) -> None:
        pass
