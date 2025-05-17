import pytest

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


@pytest.mark.asyncio
async def test_route_create_user_doc(make_request=make_request, user=test_user):
    """route: create user doc"""
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


@pytest.mark.asyncio
async def test_route_create_agent_doc(make_request=make_request, agent=test_agent):
    """route: create agent doc"""
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


@pytest.mark.asyncio
async def test_route_create_agent_doc_with_duplicate_title_should_fail(make_request=make_request, agent=test_agent, user=test_user):
    """route: create agent doc with duplicate title should fail"""
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


@pytest.mark.asyncio
async def test_route_delete_doc(make_request=make_request, agent=test_agent):
    """route: delete doc"""
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


@pytest.mark.asyncio
async def test_route_get_doc(make_request=make_request, agent=test_agent):
    """route: get doc"""
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


def test_route_list_user_docs(make_request=make_request, user=test_user):
    """route: list user docs"""
    response = make_request(
        method="GET",
        url=f"/users/{user.id}/docs",
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


def test_route_list_agent_docs(make_request=make_request, agent=test_agent):
    """route: list agent docs"""
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id}/docs",
    )

    assert response.status_code == 200
    response = response.json()
    docs = response["items"]

    assert isinstance(docs, list)


def test_route_list_user_docs_with_metadata_filter(make_request=make_request, user=test_user):
    """route: list user docs with metadata filter"""
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


def test_route_list_agent_docs_with_metadata_filter(make_request=make_request, agent=test_agent):
    """route: list agent docs with metadata filter"""
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


@pytest.mark.asyncio
async def test_route_search_agent_docs(make_request=make_request, agent=test_agent, doc=test_doc):
    """route: search agent docs"""
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


@pytest.mark.asyncio
async def test_route_search_user_docs(make_request=make_request, user=test_user, doc=test_user_doc):
    """route: search user docs"""
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


@pytest.mark.asyncio
async def test_route_search_agent_docs_hybrid_with_mmr(make_request=make_request, agent=test_agent, doc=test_doc_with_embedding):
    """route: search agent docs hybrid with mmr"""
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


@pytest.mark.asyncio
async def test_routes_embed_route(
    """routes: embed route"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_agent_docs(make_request=make_request, agent=test_agent):
    """route: bulk delete agent docs"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_user_docs_metadata_filter(make_request=make_request, user=test_user):
    """route: bulk delete user docs - metadata filter"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_agent_docs_delete_all_true(make_request=make_request, agent=test_agent):
    """route: bulk delete agent docs - delete_all=true"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_agent_docs_delete_all_false(make_request=make_request, agent=test_agent):
    """route: bulk delete agent docs - delete_all=false"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_user_docs_delete_all_true(make_request=make_request, user=test_user):
    """route: bulk delete user docs - delete_all=true"""
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


@pytest.mark.asyncio
async def test_route_bulk_delete_user_docs_delete_all_false(make_request=make_request, user=test_user):
    """route: bulk delete user docs - delete_all=false"""
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
