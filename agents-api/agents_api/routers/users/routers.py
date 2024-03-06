from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import UUID4, BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED

from agents_api.clients.cozo import client
from agents_api.clients.embed import embed
from agents_api.models.user.create_user import create_user_query
from agents_api.models.user.list_users import list_users_query
from agents_api.models.user.update_user import update_user_query
from agents_api.models.user.get_user import get_user_query
from agents_api.models.docs.create_docs import (
    create_docs_query,
)
from agents_api.models.docs.list_docs import (
    list_docs_snippets_by_owner_query,
)
from agents_api.models.docs.delete_docs import (
    delete_docs_by_id_query,
)
from agents_api.models.docs.get_docs import (
    get_docs_snippets_by_id_query,
)
from agents_api.models.docs.embed_docs import (
    embed_docs_snippets_query,
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
)


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
    # TODO: add 404 handling
    client.rm(
        "users",
        {
            "user_id": str(user_id),
            "developer_id": str(x_developer_id),
        },
    )

    return ResourceDeletedResponse(id=user_id, deleted_at=datetime.now())


@router.put("/users/{user_id}", tags=["users"])
async def update_user(
    user_id: UUID4,
    request: UpdateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = client.run(
            update_user_query(
                developer_id=x_developer_id,
                user_id=user_id,
                name=request.name,
                about=request.about,
                metadata=request.metadata or {},
            )
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


@router.get("/users/{user_id}", tags=["users"])
async def get_user_details(
    user_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> User:
    try:
        resp = [
            row.to_dict()
            for _, row in client.run(
                get_user_query(
                    developer_id=x_developer_id,
                    user_id=user_id,
                )
            ).iterrows()
        ][0]

        return User(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    request: CreateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    resp = client.run(
        create_user_query(
            developer_id=x_developer_id,
            user_id=uuid4(),
            name=request.name,
            about=request.about,
            metadata=request.metadata or {},
        ),
    )

    new_user_id = resp["user_id"][0]
    res = ResourceCreatedResponse(
        id=new_user_id,
        created_at=resp["created_at"][0],
    )

    if request.docs:
        client.run(
            "\n".join(
                [
                    create_docs_query(
                        owner_type="user",
                        owner_id=new_user_id,
                        id=uuid4(),
                        title=info.title,
                        content=info.content,
                        metadata=info.metadata,
                    )
                    for info in request.docs
                ]
            )
        )

    return res


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> UserList:
    return UserList(
        items=[
            User(**row.to_dict())
            for _, row in client.run(
                list_users_query(
                    developer_id=x_developer_id,
                    limit=limit,
                    offset=offset,
                ),
            ).iterrows()
        ]
    )


@router.post("/users/{user_id}/docs", tags=["users"])
async def create_docs(user_id: UUID4, request: CreateDoc) -> ResourceCreatedResponse:
    doc_id = uuid4()
    resp = client.run(
        create_docs_query(
            owner_type="user",
            owner_id=user_id,
            id=doc_id,
            title=request.title,
            content=request.content,
            metadata=request.metadata or {},
        )
    )

    doc_id = resp["doc_id"][0]
    res = ResourceCreatedResponse(
        id=doc_id,
        created_at=resp["created_at"][0],
    )

    indices, snippets = list(zip(*enumerate(request.content.split("\n\n"))))
    embeddings = await embed(
        [
            snippet_embed_instruction + request.title + "\n\n" + snippet
            for snippet in snippets
        ]
    )

    client.run(
        embed_docs_snippets_query(
            doc_id=doc_id,
            snippet_indices=indices,
            embeddings=embeddings,
        )
    )

    return res


@router.get("/users/{user_id}/docs", tags=["users"])
async def list_docs(user_id: UUID4, limit: int = 100, offset: int = 0) -> DocsList:
    resp = client.run(
        list_docs_snippets_by_owner_query(
            owner_type="user",
            owner_id=user_id,
        )
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
    resp = client.run(
        get_docs_snippets_by_id_query(
            owner_type="user",
            doc_id=doc_id,
        )
    )
    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docs not found",
        )

    client.run(
        delete_docs_by_id_query(
            owner_type="user",
            owner_id=user_id,
            doc_id=doc_id,
        )
    )

    return ResourceDeletedResponse(id=doc_id, deleted_at=datetime.now())
