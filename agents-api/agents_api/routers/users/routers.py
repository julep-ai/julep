import json
from json import JSONDecodeError
from typing import Annotated
from uuid import uuid4

from agents_api.autogen.openapi_model import ContentItem
from fastapi import APIRouter, HTTPException, status, Depends
import pandas as pd
from pycozo.client import QueryException
from pydantic import UUID4, BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED

from agents_api.clients.cozo import client
from agents_api.common.utils.datetime import utcnow
from agents_api.common.exceptions.users import UserNotFoundError, UserDocNotFoundError
from agents_api.models.user.create_user import create_user_query
from agents_api.models.user.list_users import list_users_query
from agents_api.models.user.update_user import update_user_query
from agents_api.models.user.patch_user import patch_user_query
from agents_api.models.user.get_user import get_user_query
from agents_api.models.docs.create_docs import (
    create_docs_query,
)
from agents_api.models.docs.list_docs import (
    list_docs_snippets_by_owner_query,
    ensure_owner_exists_query,
)
from agents_api.models.docs.delete_docs import (
    delete_docs_by_id_query,
)
from agents_api.models.docs.get_docs import (
    get_docs_snippets_by_id_query,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.autogen.openapi_model import (
    User,
    CreateUserRequest,
    UpdateUserRequest,
    ResourceCreatedResponse,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    CreateDoc,
    Doc,
    PatchUserRequest,
)
from ...clients.temporal import run_embed_docs_task


class UserList(BaseModel):
    items: list[User]


class DocsList(BaseModel):
    items: list[Doc]


router = APIRouter()
snippet_embed_instruction = "Encode this passage for retrieval: "


@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED, tags=["users"])
async def delete_user(
    user_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        client.rm(
            "users",
            {
                "user_id": str(user_id),
                "developer_id": str(x_developer_id),
            },
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code == "transact::assertion_failure":
            raise UserNotFoundError(x_developer_id, user_id)

        raise

    return ResourceDeletedResponse(id=user_id, deleted_at=utcnow())


@router.put("/users/{user_id}", tags=["users"])
async def update_user(
    user_id: UUID4,
    request: UpdateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = update_user_query(
            developer_id=x_developer_id,
            user_id=user_id,
            name=request.name,
            about=request.about,
            metadata=request.metadata,
        )

        return ResourceUpdatedResponse(
            id=resp["user_id"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code in ("transact::assertion_failure", "eval::assert_some_failure"):
            raise UserNotFoundError(x_developer_id, user_id)

        raise


@router.patch("/users/{user_id}", tags=["users"])
async def patch_user(
    user_id: UUID4,
    request: PatchUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = patch_user_query(
            developer_id=x_developer_id,
            user_id=user_id,
            name=request.name,
            about=request.about,
            metadata=request.metadata,
        )

        return ResourceUpdatedResponse(
            id=resp["user_id"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code == "transact::assertion_failure":
            raise UserNotFoundError(x_developer_id, user_id)

        raise


@router.get("/users/{user_id}", tags=["users"])
async def get_user_details(
    user_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> User:
    try:
        resp = [
            row.to_dict()
            for _, row in get_user_query(
                developer_id=x_developer_id,
                user_id=user_id,
            ).iterrows()
        ][0]

        return User(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code == "transact::assertion_failure":
            raise UserNotFoundError(x_developer_id, user_id)

        raise


@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    request: CreateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    resp = create_user_query(
        developer_id=x_developer_id,
        user_id=uuid4(),
        name=request.name,
        about=request.about or "",
        metadata=request.metadata or {},
    )

    new_user_id = resp["user_id"][0]
    docs = request.docs or []
    job_ids = [uuid4()] * len(docs)
    for job_id, doc in zip(job_ids, docs):
        content = [
            (c.model_dump() if isinstance(c, ContentItem) else c)
            for c in ([doc.content] if isinstance(doc.content, str) else doc.content)
        ]
        docs_resp = create_docs_query(
            owner_type="user",
            owner_id=new_user_id,
            id=uuid4(),
            title=doc.title,
            content=content,
            metadata=doc.metadata or {},
        )

        doc_id = docs_resp["doc_id"][0]

        await run_embed_docs_task(
            doc_id=doc_id, title=doc.title, content=content, job_id=job_id
        )

    return ResourceCreatedResponse(
        id=new_user_id,
        created_at=resp["created_at"][0],
        jobs=set(job_ids),
    )


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    metadata_filter: str = "{}",
) -> UserList:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    return UserList(
        items=[
            User(**row.to_dict())
            for _, row in list_users_query(
                developer_id=x_developer_id,
                limit=limit,
                offset=offset,
                metadata_filter=metadata_filter,
            ).iterrows()
        ]
    )


@router.post("/users/{user_id}/docs", tags=["users"])
async def create_docs(user_id: UUID4, request: CreateDoc) -> ResourceCreatedResponse:
    doc_id = uuid4()
    content = [
        (c.model_dump() if isinstance(c, ContentItem) else c)
        for c in (
            [request.content] if isinstance(request.content, str) else request.content
        )
    ]
    resp: pd.DataFrame = create_docs_query(
        owner_type="user",
        owner_id=user_id,
        id=doc_id,
        title=request.title,
        content=content,
        metadata=request.metadata or {},
    )

    job_id = uuid4()
    doc_id = resp["doc_id"][0]
    res = ResourceCreatedResponse(
        id=doc_id,
        created_at=resp["created_at"][0],
        jobs={job_id},
    )

    await run_embed_docs_task(
        doc_id=doc_id, title=request.title, content=content, job_id=job_id
    )

    return res


@router.get("/users/{user_id}/docs", tags=["users"])
async def list_docs(
    user_id: UUID4, limit: int = 100, offset: int = 0, metadata_filter: str = "{}"
) -> DocsList:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    if not len(list(ensure_owner_exists_query("user", user_id).iterrows())):
        raise UserNotFoundError("", user_id)

    resp = list_docs_snippets_by_owner_query(
        owner_type="user",
        owner_id=user_id,
        metadata_filter=metadata_filter,
    )

    return DocsList(
        items=[
            Doc(
                id=row["doc_id"],
                title=row["title"],
                content=row["snippet"],
                created_at=row["created_at"],
                metadata=row.get("metadata"),
            )
            for _, row in resp.iterrows()
        ]
    )


@router.delete("/users/{user_id}/docs/{doc_id}", tags=["users"])
async def delete_docs(user_id: UUID4, doc_id: UUID4) -> ResourceDeletedResponse:
    resp = get_docs_snippets_by_id_query(
        owner_type="user",
        doc_id=doc_id,
    )

    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docs not found",
        )

    try:
        delete_docs_by_id_query(
            owner_type="user",
            owner_id=user_id,
            doc_id=doc_id,
        )

    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise UserDocNotFoundError(user_id, doc_id)

        raise

    return ResourceDeletedResponse(id=doc_id, deleted_at=utcnow())
