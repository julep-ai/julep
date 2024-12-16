# Tests for agent queries

from uuid_extensions import uuid7
from ward import raises, test

from agents_api.common.protocol.developers import Developer
from agents_api.queries.developers.get_developer import get_developer # , verify_developer
from .fixtures import pg_client, test_developer_id


@test("query: get developer not exists")
def _(client=pg_client):
    with raises(Exception):
        get_developer(
            developer_id=uuid7(),
            client=client,
        )


# @test("query: get developer")
# def _(client=pg_client, developer_id=test_developer_id):
#     developer = get_developer(
#         developer_id=developer_id,
#         client=client,
#     )

#     assert isinstance(developer, Developer)
#     assert developer.id


# @test("query: verify developer exists")
# def _(client=cozo_client, developer_id=test_developer_id):
#     verify_developer(
#         developer_id=developer_id,
#         client=client,
#     )


# @test("query: verify developer not exists")
# def _(client=cozo_client):
#     with raises(Exception):
#         verify_developer(
#             developer_id=uuid7(),
#             client=client,
#         )
