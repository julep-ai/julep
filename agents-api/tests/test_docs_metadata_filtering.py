"""
Tests for secure metadata filtering in docs queries
"""

from agents_api.autogen.Docs import BulkDeleteDocsRequest, CreateDocRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.docs.bulk_delete_docs import bulk_delete_docs
from agents_api.queries.docs.create_doc import create_doc
from agents_api.queries.docs.list_docs import list_docs
import pytest


async def test_query_list_docs_with_sql_injection_attempt_in_metadata_filter(pg_dsn, test_developer, test_agent):
    """Test that list_docs safely handles metadata filters with SQL injection attempts."""
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a test document with normal metadata
    doc_normal = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Test Doc Normal",
            content="Test content for normal doc",
            metadata={"test_key": "test_value"},
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Create a test document with a special key that might be used in SQL injection
    doc_special = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Test Doc Special",
            content="Test content for special doc",
            metadata={"special; SELECT * FROM agents--": "special_value"},
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Attempt normal metadata filtering
    docs_normal = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        metadata_filter={"test_key": "test_value"},
        connection_pool=pool,
    )

    # Verify normal filtering works
    assert any(d.id == doc_normal.id for d in docs_normal)
    assert not any(d.id == doc_special.id for d in docs_normal)

    # Attempt filtering with injection attempt
    injection_filters = [
        {"key' OR 1=1--": "value"},  # SQL injection in key
        {"key": "1' OR '1'='1"},  # SQL injection in value
        {"key; DROP TABLE users--": "value"},  # Command injection in key
    ]

    for injection_filter in injection_filters:
        # These should safely execute without error, returning no results
        docs_injection = await list_docs(
            developer_id=test_developer.id,
            owner_type="agent",
            owner_id=test_agent.id,
            metadata_filter=injection_filter,
            connection_pool=pool,
        )

        # Verify we don't get unexpected results
        assert len(docs_injection) == 0, (
            f"Should not match any docs with injection filter: {injection_filter}"
        )

    # Test exact matching for the special key metadata
    docs_special = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        metadata_filter={"special; SELECT * FROM agents--": "special_value"},
        connection_pool=pool,
    )

    # Verify exact matching works for special characters too
    assert any(d.id == doc_special.id for d in docs_special)
    assert not any(d.id == doc_normal.id for d in docs_special)


async def test_query_bulk_delete_docs_with_sql_injection_attempt_in_metadata_filter(pg_dsn, test_developer, test_user):
    """Test that bulk_delete_docs safely handles metadata filters with SQL injection attempts."""
    pool = await create_db_pool(dsn=pg_dsn)

    # Create test documents with different metadata patterns
    doc1 = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Doc for deletion test 1",
            content="Content for deletion test 1",
            metadata={"delete_key": "delete_value"},
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    doc2 = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Doc for deletion test 2",
            content="Content for deletion test 2",
            metadata={"keep_key": "keep_value"},
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    doc3 = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Doc for deletion test 3",
            content="Content for deletion test 3",
            metadata={"special' DELETE FROM docs--": "special_value"},
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Verify all docs exist
    all_docs = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    doc_ids = [d.id for d in all_docs]
    assert doc1.id in doc_ids
    assert doc2.id in doc_ids
    assert doc3.id in doc_ids

    # Delete with normal metadata filter
    await bulk_delete_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        data=BulkDeleteDocsRequest(
            metadata_filter={"delete_key": "delete_value"},
            delete_all=False,
        ),
        connection_pool=pool,
    )

    # Verify only matching doc was deleted
    remaining_docs = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    remaining_ids = [d.id for d in remaining_docs]
    assert doc1.id not in remaining_ids  # Should be deleted
    assert doc2.id in remaining_ids  # Should still exist
    assert doc3.id in remaining_ids  # Should still exist

    # Attempt deletion with injection metadata
    injection_filters = [
        {"key' OR 1=1--": "value"},  # SQL injection in key
        {"key": "1' OR '1'='1; DELETE FROM docs"},  # SQL injection in value
    ]

    for injection_filter in injection_filters:
        # These should execute without deleting unexpected docs
        await bulk_delete_docs(
            developer_id=test_developer.id,
            owner_type="user",
            owner_id=test_user.id,
            data=BulkDeleteDocsRequest(
                metadata_filter=injection_filter,
                delete_all=False,
            ),
            connection_pool=pool,
        )

    # Verify other docs still exist
    still_remaining_docs = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    still_remaining_ids = [d.id for d in still_remaining_docs]
    assert doc2.id in still_remaining_ids  # Should still exist
    assert doc3.id in still_remaining_ids  # Should still exist

    # Delete doc with special characters in metadata
    await bulk_delete_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        data=BulkDeleteDocsRequest(
            metadata_filter={"special' DELETE FROM docs--": "special_value"},
            delete_all=False,
        ),
        connection_pool=pool,
    )

    # Verify special doc was deleted
    final_docs = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    final_ids = [d.id for d in final_docs]
    assert doc3.id not in final_ids  # Should be deleted
    assert doc2.id in final_ids  # Should still exist
