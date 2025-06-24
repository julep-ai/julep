from .utils import patch_testing_temporal


async def test_route_create_user_doc(make_request, test_user):
    async with patch_testing_temporal():
        data = {"title": "Test User Doc", "content": ["This is a test user document."]}
        response = make_request(
            method="POST", url=f"/users/{test_user.id}/docs", json=data
        )
        assert response.status_code == 201


async def test_route_create_agent_doc(make_request, test_agent):
    async with patch_testing_temporal():
        data = {
            "title": "Test Agent Doc",
            "content": ["This is a test agent document."],
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 201


async def test_route_create_agent_doc_with_duplicate_title_should_fail(
    make_request, test_agent, test_user
):
    async with patch_testing_temporal():
        data = {
            "title": "Test Duplicate Doc",
            "content": ["This is a test duplicate document."],
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 201
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 409
        response = make_request(
            method="POST", url=f"/users/{test_user.id}/docs", json=data
        )
        assert response.status_code == 201


async def test_route_delete_doc(make_request, test_agent):
    async with patch_testing_temporal():
        data = {"title": "Test Agent Doc", "content": "This is a test agent document."}
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        doc_id = response.json()["id"]
        response = make_request(method="GET", url=f"/docs/{doc_id}")
        assert response.status_code == 200
        assert response.json()["id"] == doc_id
        assert response.json()["title"] == "Test Agent Doc"
        assert response.json()["content"] == ["This is a test agent document."]
        response = make_request(
            method="DELETE", url=f"/agents/{test_agent.id}/docs/{doc_id}"
        )
        assert response.status_code == 202
        response = make_request(method="GET", url=f"/docs/{doc_id}")
        assert response.status_code == 404


async def test_route_get_doc(make_request, test_agent):
    async with patch_testing_temporal():
        data = {
            "title": "Test Agent Doc",
            "content": ["This is a test agent document."],
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        doc_id = response.json()["id"]
        response = make_request(method="GET", url=f"/docs/{doc_id}")
        assert response.status_code == 200


def test_route_list_user_docs(make_request, test_user):
    """route: list user docs"""
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    response = response.json()
    docs = response["items"]
    assert isinstance(docs, list)


def test_route_list_agent_docs(make_request, test_agent):
    """route: list agent docs"""
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    response = response.json()
    docs = response["items"]
    assert isinstance(docs, list)


def test_route_list_user_docs_with_metadata_filter(make_request, test_user):
    """route: list user docs with metadata filter"""
    response = make_request(
        method="GET",
        url=f"/users/{test_user.id}/docs",
        params={"metadata_filter": {"test": "test"}},
    )
    assert response.status_code == 200
    response = response.json()
    docs = response["items"]
    assert isinstance(docs, list)


def test_route_list_agent_docs_with_metadata_filter(make_request, test_agent):
    """route: list agent docs with metadata filter"""
    response = make_request(
        method="GET",
        url=f"/agents/{test_agent.id}/docs",
        params={"metadata_filter": {"test": "test"}},
    )
    assert response.status_code == 200
    response = response.json()
    docs = response["items"]
    assert isinstance(docs, list)


async def test_route_search_agent_docs(make_request, test_agent, test_doc):
    search_params = {"text": test_doc.content[0], "limit": 1}
    response = make_request(
        method="POST", url=f"/agents/{test_agent.id}/search", json=search_params
    )
    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]
    assert isinstance(docs, list)
    assert len(docs) >= 1


async def test_route_search_user_docs(make_request, test_user, test_user_doc):
    search_params = {"text": test_user_doc.content[0], "limit": 1}
    response = make_request(
        method="POST", url=f"/users/{test_user.id}/search", json=search_params
    )
    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]
    assert isinstance(docs, list)
    assert len(docs) >= 1


async def test_route_search_agent_docs_hybrid_with_mmr(
    make_request, test_agent, test_doc_with_embedding
):
    EMBEDDING_SIZE = 1024
    search_params = {
        "text": test_doc_with_embedding.content[0],
        "vector": [1.0] * EMBEDDING_SIZE,
        "mmr_strength": 0.5,
        "limit": 1,
    }
    response = make_request(
        method="POST", url=f"/agents/{test_agent.id}/search", json=search_params
    )
    assert response.status_code == 200
    response = response.json()
    docs = response["docs"]
    assert isinstance(docs, list)
    assert len(docs) >= 1


async def test_routes_embed_route(make_request, patch_embed_acompletion):
    embed, _ = patch_embed_acompletion
    response = make_request(method="POST", url="/embed", json={"text": "blah blah"})
    result = response.json()
    assert "vectors" in result
    embed.assert_called()


async def test_route_bulk_delete_agent_docs(make_request, test_agent):
    for i in range(3):
        data = {
            "title": f"Bulk Test Doc {i}",
            "content": ["This is a test document for bulk deletion."],
            "metadata": {"bulk_test": "true", "index": str(i)},
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 201
    data = {
        "title": "Non Bulk Test Doc",
        "content": ["This document should not be deleted."],
        "metadata": {"bulk_test": "false"},
    }
    response = make_request(
        method="POST", url=f"/agents/{test_agent.id}/docs", json=data
    )
    assert response.status_code == 201
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    assert len(docs_before) >= 4
    response = make_request(
        method="DELETE",
        url=f"/agents/{test_agent.id}/docs",
        json={"metadata_filter": {"bulk_test": "true"}},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 3
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == len(docs_before) - 3


async def test_route_bulk_delete_user_docs_metadata_filter(make_request, test_user):
    for i in range(2):
        data = {
            "title": f"User Bulk Test Doc {i}",
            "content": ["This is a user test document for bulk deletion."],
            "metadata": {"user_bulk_test": "true", "index": str(i)},
        }
        response = make_request(
            method="POST", url=f"/users/{test_user.id}/docs", json=data
        )
        assert response.status_code == 201
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    response = make_request(
        method="DELETE",
        url=f"/users/{test_user.id}/docs",
        json={"metadata_filter": {"user_bulk_test": "true"}},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 2
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == len(docs_before) - 2


async def test_route_bulk_delete_agent_docs_delete_all_true(make_request, test_agent):
    for i in range(3):
        data = {
            "title": f"Delete All Test Doc {i}",
            "content": ["This is a test document for delete_all."],
            "metadata": {"test_type": "delete_all_test", "index": str(i)},
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 201
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 3
    response = make_request(
        method="DELETE", url=f"/agents/{test_agent.id}/docs", json={"delete_all": True}
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == 0


async def test_route_bulk_delete_agent_docs_delete_all_false(make_request, test_agent):
    for i in range(2):
        data = {
            "title": f"Safety Test Doc {i}",
            "content": ["This document should not be deleted by empty filter."],
            "metadata": {"test_type": "safety_test"},
        }
        response = make_request(
            method="POST", url=f"/agents/{test_agent.id}/docs", json=data
        )
        assert response.status_code == 201
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2
    response = make_request(
        method="DELETE",
        url=f"/agents/{test_agent.id}/docs",
        json={"metadata_filter": {}, "delete_all": False},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 0
    response = make_request(method="GET", url=f"/agents/{test_agent.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == initial_count


async def test_route_bulk_delete_user_docs_delete_all_true(make_request, test_user):
    for i in range(2):
        data = {
            "title": f"User Delete All Test {i}",
            "content": ["This is a user test document for delete_all."],
            "metadata": {"test_type": "user_delete_all_test"},
        }
        response = make_request(
            method="POST", url=f"/users/{test_user.id}/docs", json=data
        )
        assert response.status_code == 201
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2
    response = make_request(
        method="DELETE", url=f"/users/{test_user.id}/docs", json={"delete_all": True}
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == 0


async def test_route_bulk_delete_user_docs_delete_all_false(make_request, test_user):
    for i in range(2):
        data = {
            "title": f"User Safety Test Doc {i}",
            "content": ["This user document should not be deleted by empty filter."],
            "metadata": {"test_type": "user_safety_test"},
        }
        response = make_request(
            method="POST", url=f"/users/{test_user.id}/docs", json=data
        )
        assert response.status_code == 201
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_before = response.json()["items"]
    initial_count = len(docs_before)
    assert initial_count >= 2
    response = make_request(
        method="DELETE",
        url=f"/users/{test_user.id}/docs",
        json={"metadata_filter": {}, "delete_all": False},
    )
    assert response.status_code == 202
    deleted_response = response.json()
    assert isinstance(deleted_response["items"], list)
    assert len(deleted_response["items"]) == 0
    response = make_request(method="GET", url=f"/users/{test_user.id}/docs")
    assert response.status_code == 200
    docs_after = response.json()["items"]
    assert len(docs_after) == initial_count
