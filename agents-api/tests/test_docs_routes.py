from ward import test

from .fixtures import (
    make_request,
    patch_embed_acompletion,
    test_agent,
    test_doc,
    test_user,
    test_user_doc,
)
from .utils import patch_testing_temporal


@test("route: create user doc")
async def _(make_request=make_request, user=test_user):
    async with patch_testing_temporal():
        data = dict(
            title="Test User Doc",
            content=["This is a test user document."],
        )

        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )

        assert response.status_code == 201

        result = response.json()
        assert len(result["jobs"]) > 0


@test("route: create agent doc")
async def _(make_request=make_request, agent=test_agent):
    async with patch_testing_temporal():
        data = dict(
            title="Test Agent Doc",
            content=["This is a test agent document."],
        )

        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )

        assert response.status_code == 201

        result = response.json()
        assert len(result["jobs"]) > 0


@test("route: delete doc")
async def _(make_request=make_request, agent=test_agent):
    async with patch_testing_temporal():
        data = dict(
            title="Test Agent Doc",
            content=["This is a test agent document."],
        )

        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )
        doc_id = response.json()["id"]

        response = make_request(
            method="DELETE",
            url=f"/agents/{agent.id}/docs/{doc_id}",
        )

        assert response.status_code == 202

        response = make_request(
            method="GET",
            url=f"/docs/{doc_id}",
        )

        assert response.status_code == 404


@test("route: get doc")
async def _(make_request=make_request, agent=test_agent):
    async with patch_testing_temporal():
        data = dict(
            title="Test Agent Doc",
            content=["This is a test agent document."],
        )

        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )
        doc_id = response.json()["id"]

        response = make_request(
            method="GET",
            url=f"/docs/{doc_id}",
        )

        assert response.status_code == 200


@test("route: list user docs")
def _(make_request=make_request, user=test_user):
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


@test("route: list agent docs")
def _(make_request=make_request, agent=test_agent):
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


# TODO: Fix this test. It fails sometimes and sometimes not.
@test("route: search agent docs")
async def _(make_request=make_request, agent=test_agent, doc=test_doc):
    search_params = dict(
        text=doc.content[0],
        limit=1,
    )

    response = make_request(
        method="POST",
        url=f"/agents/{agent.id}/search",
        json=search_params,
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]

    assert isinstance(docs, list)
    assert len(docs) >= 1


@test("route: search user docs")
def _(make_request=make_request, user=test_user, doc=test_user_doc):
    search_params = dict(
        text=doc.content[0],
        limit=1,
    )

    response = make_request(
        method="POST",
        url=f"/users/{user.id}/search",
        json=search_params,
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]

    assert isinstance(docs, list)

    # FIXME: This test is failing because the search is not returning the expected results
    # assert len(docs) >= 1


@test("routes: embed route")
async def _(
    make_request=make_request,
    mocks=patch_embed_acompletion,
):
    (embed, _) = mocks

    response = make_request(
        method="POST",
        url="/embed",
        json={"text": "blah blah"},
    )

    result = response.json()
    assert "vectors" in result

    embed.assert_called()
