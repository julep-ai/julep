from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Union, Dict

from ..api.types import (
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    Session,
    ListSessionsResponse,
    ChatSettingsStop,
    ChatSettingsResponseFormat,
    InputChatMlMessage,
    ChatMlMessage,
    ToolChoiceOption,
    Tool,
    ChatResponse,
    GetSuggestionsResponse,
    GetHistoryResponse,
    Suggestion,
)

from .base import BaseManager
from .utils import is_valid_uuid4


class BaseSessionsManager(BaseManager):
    def _get(self, id: Union[str, UUID]) -> Union[Session, Awaitable[Session]]:
        assert is_valid_uuid4(id), "id must be a valid UUID v4"
        return self.api_client.get_session(session_id=id)

    def _create(
        self,
        user_id: Union[str, UUID],
        agent_id: Union[str, UUID],
        situation: Optional[str] = None,
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        # Cast instructions to a list of Instruction objects
        assert is_valid_uuid4(user_id) and is_valid_uuid4(
            agent_id
        ), "id must be a valid UUID v4"

        return self.api_client.create_session(
            user_id=user_id,
            agent_id=agent_id,
            situation=situation,
        )

    def _list_items(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Union[ListSessionsResponse, Awaitable[ListSessionsResponse]]:
        return self.api_client.list_sessions(
            limit=limit,
            offset=offset,
        )

    def _delete(self, session_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
        assert is_valid_uuid4(session_id), "id must be a valid UUID v4"
        return self.api_client.delete_session(session_id=session_id)

    def _update(
        self,
        session_id: Union[str, UUID],
        situation: str,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        assert is_valid_uuid4(session_id), "id must be a valid UUID v4"

        return self.api_client.update_session(
            session_id=session_id,
            situation=situation,
        )

    def _chat(
        self,
        *,
        session_id: str,
        messages: List[InputChatMlMessage],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[ToolChoiceOption] = None,
        frequency_penalty: Optional[float] = None,
        length_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, Optional[int]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        response_format: Optional[ChatSettingsResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Optional[ChatSettingsStop] = None,
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        recall: Optional[bool] = None,
        remember: Optional[bool] = None,
    ) -> Union[ChatResponse, Awaitable[ChatResponse]]:
        return self.api_client.chat(
            session_id=session_id,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            frequency_penalty=frequency_penalty,
            length_penalty=length_penalty,
            logit_bias=logit_bias,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            recall=recall,
            remember=remember,
        )

    def _suggestions(
        self,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetSuggestionsResponse, Awaitable[GetSuggestionsResponse]]:
        return self.api_client.get_suggestions(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

    def _history(
        self,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetHistoryResponse, Awaitable[GetHistoryResponse]]:
        return self.api_client.get_history(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )


class SessionsManager(BaseSessionsManager):
    @beartype
    def get(self, id: Union[str, UUID]) -> Session:
        return self._get(id=id)

    @beartype
    def create(
        self,
        *,
        user_id: Union[str, UUID],
        agent_id: Union[str, UUID],
        situation: Optional[str] = None,
    ) -> ResourceCreatedResponse:
        return self._create(
            user_id=user_id,
            agent_id=agent_id,
            situation=situation,
        )

    @beartype
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Session]:
        return self._list_items(
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def delete(self, session_id: Union[str, UUID]):
        return self._delete(session_id=session_id)

    @beartype
    def update(
        self,
        *,
        session_id: Union[str, UUID],
        situation: str,
    ) -> ResourceUpdatedResponse:
        return self._update(
            session_id=session_id,
            situation=situation,
        )

    @beartype
    def chat(
        self,
        *,
        session_id: str,
        messages: List[InputChatMlMessage],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[ToolChoiceOption] = None,
        frequency_penalty: Optional[float] = None,
        length_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, Optional[int]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        response_format: Optional[ChatSettingsResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Optional[ChatSettingsStop] = None,
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        recall: Optional[bool] = None,
        remember: Optional[bool] = None,
    ) -> ChatResponse:
        return self._chat(
            session_id=session_id,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            frequency_penalty=frequency_penalty,
            length_penalty=length_penalty,
            logit_bias=logit_bias,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            recall=recall,
            remember=remember,
        )

    @beartype
    def suggestions(
        self,
        *,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Suggestion]:
        return self._suggestions(
            session_id=session_id,
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def history(
        self,
        *,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ChatMlMessage]:
        return self._history(
            session_id=session_id,
            limit=limit,
            offset=offset,
        ).items


class AsyncSessionsManager(BaseSessionsManager):
    @beartype
    async def get(self, id: Union[UUID, str]) -> Session:
        return await self._get(id=id)

    @beartype
    async def create(
        self,
        *,
        user_id: Union[str, UUID],
        agent_id: Union[str, UUID],
        situation: Optional[str] = None,
    ) -> ResourceCreatedResponse:
        return await self._create(
            user_id=user_id,
            agent_id=agent_id,
            situation=situation,
        )

    @beartype
    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Session]:
        return (
            await self._list_items(
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def delete(self, session_id: Union[str, UUID]):
        return await self._delete(session_id=session_id)

    @beartype
    async def update(
        self,
        *,
        session_id: Union[str, UUID],
        situation: str,
    ) -> ResourceUpdatedResponse:
        return await self._update(
            session_id=session_id,
            situation=situation,
        )

    @beartype
    async def chat(
        self,
        *,
        session_id: str,
        messages: List[InputChatMlMessage],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[ToolChoiceOption] = None,
        frequency_penalty: Optional[float] = None,
        length_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, Optional[int]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        response_format: Optional[ChatSettingsResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Optional[ChatSettingsStop] = None,
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        recall: Optional[bool] = None,
        remember: Optional[bool] = None,
    ) -> ChatResponse:
        return await self._chat(
            session_id=session_id,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            frequency_penalty=frequency_penalty,
            length_penalty=length_penalty,
            logit_bias=logit_bias,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            recall=recall,
            remember=recall,
        )

    @beartype
    async def suggestions(
        self,
        *,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Suggestion]:
        return (
            await self._suggestions(
                session_id=session_id,
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def history(
        self,
        *,
        session_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ChatMlMessage]:
        return (
            await self._history(
                session_id=session_id,
                limit=limit,
                offset=offset,
            )
        ).items
