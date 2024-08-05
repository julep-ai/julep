# import uuid

# from julep.api import ResourceCreatedResponse, ResourceUpdatedResponse, User
# from julep.api.core import ApiError
# from ward import test

# from tests.fixtures import async_client, client, user


# @test("create user")
# def _(client=client):
#     response = client.users.create(
#         name="test user",
#         about="test user about",
#     )

#     assert isinstance(response, ResourceCreatedResponse)
#     assert response.created_at
#     assert bool(uuid.UUID(str(response.id), version=4))


# @test("async create user")
# async def _(client=async_client):
#     response = await client.users.create(
#         name="test user",
#         about="test user about",
#     )

#     assert isinstance(response, ResourceCreatedResponse)
#     assert response.created_at
#     assert bool(uuid.UUID(str(response.id), version=4))


# @test("get existing user")
# def _(existing_user=user, client=client):
#     response = client.users.get(existing_user.id)
#     assert isinstance(response, User)
#     assert existing_user.id == response.id


# @test("async get existing user")
# async def _(existing_user=user, client=async_client):
#     response = await client.users.get(existing_user.id)
#     assert isinstance(response, User)
#     assert existing_user.id == response.id


# @test("get non-existing user")
# def _(client=client):
#     try:
#         client.users.get(uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async get non-existing user")
# async def _(client=async_client):
#     try:
#         await client.users.get(uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("update existing user")
# def _(existing_user=user, client=client):
#     response = client.users.update(
#         user_id=existing_user.id,
#         name="test user",
#         about="test user about",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at
#     assert response.updated_at != existing_user.updated_at
#     assert response.id == existing_user.id


# @test("async update existing user")
# async def _(existing_user=user, async_client=client):
#     response = await client.users.update(
#         user_id=existing_user.id,
#         name="test user",
#         about="test user about",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at
#     assert response.updated_at != existing_user.updated_at
#     assert response.id == existing_user.id


# @test("update non-existing user")
# def _(client=client):
#     try:
#         client.users.update(
#             user_id=uuid.uuid4(),
#             name="test user",
#             about="test user about",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async update non-existing user")
# async def _(client=async_client):
#     try:
#         await client.users.update(
#             user_id=uuid.uuid4(),
#             name="test user",
#             about="test user about",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("delete existing user")
# def _(existing_user=user, client=client):
#     response = client.users.delete(
#         user_id=existing_user.id,
#     )

#     assert response is None


# @test("async delete existing user")
# async def _(existing_user=user, client=async_client):
#     response = await client.users.delete(
#         user_id=existing_user.id,
#     )

#     assert response is None


# @test("delete non-existing user")
# def _(client=client):
#     try:
#         client.users.delete(
#             user_id=uuid.uuid4(),
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async delete non-existing user")
# async def _(client=async_client):
#     try:
#         await client.users.delete(
#             user_id=uuid.uuid4(),
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("list users")
# def _(existing_user=user, client=client):
#     response = client.users.list()
#     assert len(response) > 0
#     assert isinstance(response[0], User)
#     assert response[0].id == existing_user.id


# @test("async list users")
# async def _(existing_user=user, client=async_client):
#     response = await client.users.list()
#     assert len(response) > 0
#     assert isinstance(response[0], User)
#     assert response[0].id == existing_user.id
