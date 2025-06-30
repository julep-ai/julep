from ward import test

from .fixtures import (
    make_request,
    patch_embed_acompletion,
    test_agent,
    test_doc,
    test_doc_with_embedding,
    test_user,
    test_user_doc,
)
from .utils import patch_testing_temporal


@test("route: create user doc")
async def _(make_request=make_request, user=test_user):
    async with patch_testing_temporal():
        data = {
            "title": "Test User Doc",
            "content": ["This is a test user document."],
        }

        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )

        assert response.status_code == 201


@test("route: create agent doc")
async def _(make_request=make_request, agent=test_agent):
    async with patch_testing_temporal():
        data = {
            "title": "Test Agent Doc",
            "content": ["This is a test agent document."],
        }

        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )

        assert response.status_code == 201


@test("route: create agent doc with duplicate title should fail")
async def _(make_request=make_request, agent=test_agent, user=test_user):
    async with patch_testing_temporal():
        data = {
            "title": "Test Duplicate Doc",
            "content": ["This is a test duplicate document."],
        }

        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )

        assert response.status_code == 201

        # This should fail
        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )

        assert response.status_code == 409

        # This should pass
        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )

        assert response.status_code == 201


@test("route: delete doc")
async def _(make_request=make_request, agent=test_agent):
    async with patch_testing_temporal():
        data = {
            "title": "Test Agent Doc",
            "content": "This is a test agent document.",
        }

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
        assert response.json()["id"] == doc_id
        assert response.json()["title"] == "Test Agent Doc"
        assert response.json()["content"] == ["This is a test agent document."]

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
        data = {
            "title": "Test Agent Doc",
            "content": ["This is a test agent document."],
        }

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


@test("route: list user docs with metadata filter")
def _(make_request=make_request, user=test_user):
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


@test("route: list agent docs with metadata filter")
def _(make_request=make_request, agent=test_agent):
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


@test("route: search agent docs")
async def _(make_request=make_request, agent=test_agent, doc=test_doc):
    search_params = {
        "text": doc.content[0],
        "limit": 1,
    }

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
async def _(make_request=make_request, user=test_user, doc=test_user_doc):
    search_params = {
        "text": doc.content[0],
        "limit": 1,
    }

    response = make_request(
        method="POST",
        url=f"/users/{user.id}/search",
        json=search_params,
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]

    assert isinstance(docs, list)

    assert len(docs) >= 1


@test("route: search agent docs hybrid with mmr")
async def _(make_request=make_request, agent=test_agent, doc=test_doc_with_embedding):
    EMBEDDING_SIZE = 1024
    search_params = {
        "text": doc.content[0],
        "vector": [1.0] * EMBEDDING_SIZE,
        "mmr_strength": 0.5,
        "limit": 1,
    }

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


@test("route: bulk delete agent docs")
async def _(make_request=make_request, agent=test_agent):
    for i in range(3):
        data = {
            "title": f"Bulk Test Doc {i}",
            "content": ["This is a test document for bulk deletion."],
            "metadata": {"bulk_test": "true", "index": str(i)},
        }
        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Create a doc with different metadata
    data = {
        "title": "Non Bulk Test Doc",
        "content": ["This document should not be deleted."],
        "metadata": {"bulk_test": "false"},
    }
    response = make_request(
        method="POST",
        url=f"/agents/{agent.id}/docs",
        json=data,
    )
    assert response.status_code == 201

    # Verify all docs exist
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]
    assert len(docs_before) >= 4

    # Bulk delete docs with specific metadata
    response = make_request(
        method="DELETE",
        url=f"/agents/{agent.id}/docs",
        json={"metadata_filter": {"bulk_test": "true"}},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 3

    # Verify that only the target docs were deleted
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == len(docs_before) - 3


@test("route: bulk delete user docs - metadata filter")
async def _(make_request=make_request, user=test_user):
    for i in range(2):
        data = {
            "title": f"User Bulk Test Doc {i}",
            "content": ["This is a user test document for bulk deletion."],
            "metadata": {"user_bulk_test": "true", "index": str(i)},
        }
        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Verify docs exist
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]

    # Bulk delete docs with specific metadata
    response = make_request(
        method="DELETE",
        url=f"/users/{user.id}/docs",
        json={"metadata_filter": {"user_bulk_test": "true"}},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 2

    # Verify that only the target docs were deleted
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == len(docs_before) - 2


@test("route: bulk delete agent docs - delete_all=true")
async def _(make_request=make_request, agent=test_agent):
    # Create several test docs
    for i in range(3):
        data = {
            "title": f"Delete All Test Doc {i}",
            "content": ["This is a test document for delete_all."],
            "metadata": {"test_type": "delete_all_test", "index": str(i)},
        }
        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Verify docs exist
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 3

    # Bulk delete all docs with delete_all flag
    response = make_request(
        method="DELETE",
        url=f"/agents/{agent.id}/docs",
        json={"delete_all": True},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)

    # Verify all docs were deleted
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == 0


@test("route: bulk delete agent docs - delete_all=false")
async def _(make_request=make_request, agent=test_agent):
    # Create test docs
    for i in range(2):
        data = {
            "title": f"Safety Test Doc {i}",
            "content": ["This document should not be deleted by empty filter."],
            "metadata": {"test_type": "safety_test"},
        }
        response = make_request(
            method="POST",
            url=f"/agents/{agent.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Get initial doc count
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2

    # Try to delete with empty metadata filter and delete_all=false
    response = make_request(
        method="DELETE",
        url=f"/agents/{agent.id}/docs",
        json={"metadata_filter": {}, "delete_all": False},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    # Should have deleted 0 items
    assert len(deleted_response["items"]) == 0

    # Verify no docs were deleted
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == initial_count


@test("route: bulk delete user docs - delete_all=true")
async def _(make_request=make_request, user=test_user):
    # Create test docs
    for i in range(2):
        data = {
            "title": f"User Delete All Test {i}",
            "content": ["This is a user test document for delete_all."],
            "metadata": {"test_type": "user_delete_all_test"},
        }
        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Verify docs exist
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2

    # Bulk delete all docs with delete_all flag
    response = make_request(
        method="DELETE",
        url=f"/users/{user.id}/docs",
        json={"delete_all": True},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)

    # Verify all docs were deleted
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == 0


@test("route: bulk delete user docs - delete_all=false")
async def _(make_request=make_request, user=test_user):
    # Create test docs
    for i in range(2):
        data = {
            "title": f"User Safety Test Doc {i}",
            "content": ["This user document should not be deleted by empty filter."],
            "metadata": {"test_type": "user_safety_test"},
        }
        response = make_request(
            method="POST",
            url=f"/users/{user.id}/docs",
            json=data,
        )
        assert response.status_code == 201

    # Get initial doc count
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2

    # Try to delete with empty metadata filter and delete_all=false
    response = make_request(
        method="DELETE",
        url=f"/users/{user.id}/docs",
        json={"metadata_filter": {}, "delete_all": False},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    # Should have deleted 0 items
    assert len(deleted_response["items"]) == 0

    # Verify no docs were deleted
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == initial_count
