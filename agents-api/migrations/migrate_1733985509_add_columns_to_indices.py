# /usr/bin/env python3

MIGRATION_ID = "add_columns_to_indices"
CREATED_AT = 1733985509.241258


def up(client):
    client.run(
        """
        { ::index drop executions:execution_id_status_idx }
        { ::index create executions:execution_id_status_idx { task_id, execution_id, status } }
        { ::index drop docs:owner_id_metadata_doc_id_idx }
        { ::index create docs:owner_id_metadata_doc_id_idx { owner_type, owner_id, metadata, doc_id } }
        """
    )


def down(client):
    client.run(
        """
        { ::index drop executions:execution_id_status_idx }
        { ::index create executions:execution_id_status_idx { execution_id, status } }
        { ::index drop docs:owner_id_metadata_doc_id_idx }
        { ::index create docs:owner_id_metadata_doc_id_idx { owner_id, metadata, doc_id } }
        """
    )
