from typing import Annotated
from uuid import uuid4
from pydantic import UUID4, BaseModel
from fastapi import APIRouter, HTTPException, status, Depends
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from agents_api.clients.cozo import client
from agents_api.clients.embed import embed
from agents_api.models.user.create_user import create_user_query
from agents_api.models.user.list_users import list_users_query
from agents_api.models.user.update_user import update_user_query
from agents_api.models.user.get_user import get_user_query
from agents_api.models.additional_info.create_additional_info import (
    create_additional_info_query,
)
from agents_api.models.additional_info.list_additional_info import (
    list_additional_info_snippets_by_owner_query,
)
from agents_api.models.additional_info.delete_additional_info import (
    delete_additional_info_by_id_query,
)
from agents_api.models.additional_info.get_additional_info import (
    get_additional_info_snippets_by_id_query,
)
from agents_api.models.additional_info.embed_additional_info import (
    embed_additional_info_snippets_query,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.autogen.openapi_model import (
    User,
    CreateUserRequest,
    UpdateUserRequest,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    CreateAdditionalInfoRequest,
    AdditionalInfo,
)


class UserList(BaseModel):
    items: list[User]


class AdditionalInfoList(BaseModel):
    items: list[AdditionalInfo]


router = APIRouter()
snippet_embed_instruction = "Encode this passage for retrieval: "


@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED, tags=["users"])
async def delete_user(
    user_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
):
    # TODO: add 404 handling
    client.rm(
        "users",
        {
            "user_id": str(user_id),
            "developer_id": str(x_developer_id),
        },
    )


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
        ),
    )

    new_user_id = resp["user_id"][0]
    res = ResourceCreatedResponse(
        id=new_user_id,
        created_at=resp["created_at"][0],
    )

    if request.additional_information:
        client.run(
            "\n".join(
                [
                    create_additional_info_query(
                        owner_type="user",
                        owner_id=new_user_id,
                        id=uuid4(),
                        title=info.title,
                        content=info.content,
                    )
                    for info in request.additional_information
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


@router.post("/users/{user_id}/additional_info", tags=["users"])
async def create_additional_info(
    user_id: UUID4, request: CreateAdditionalInfoRequest
) -> ResourceCreatedResponse:
    additional_info_id = uuid4()
    resp = client.run(
        create_additional_info_query(
            owner_type="user",
            owner_id=user_id,
            id=additional_info_id,
            title=request.title,
            content=request.content,
        )
    )

    additional_info_id = resp["additional_info_id"][0]
    res = ResourceCreatedResponse(
        id=additional_info_id,
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
        embed_additional_info_snippets_query(
            additional_info_id=additional_info_id,
            snippet_indices=indices,
            embeddings=embeddings,
        )
    )

    return res


@router.get("/users/{user_id}/additional_info", tags=["users"])
async def list_additional_info(
    user_id: UUID4, limit: int = 100, offset: int = 0
) -> AdditionalInfoList:
    resp = client.run(
        list_additional_info_snippets_by_owner_query(
            owner_type="user",
            owner_id=user_id,
        )
    )

    return AdditionalInfoList(
        items=[
            AdditionalInfo(
                id=row["additional_info_id"],
                title=row["title"],
                content=row["snippet"],
            )
            for _, row in resp.iterrows()
        ]
    )


@router.delete("/users/{user_id}/additional_info/{additional_info_id}", tags=["users"])
async def delete_additional_info(user_id: UUID4, additional_info_id: UUID4):
    resp = client.run(
        get_additional_info_snippets_by_id_query(
            owner_type="user",
            additional_info_id=additional_info_id,
        )
    )
    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Additional info not found",
        )

    client.run(
        delete_additional_info_by_id_query(
            owner_type="user",
            owner_id=user_id,
            additional_info_id=additional_info_id,
        )
    )
