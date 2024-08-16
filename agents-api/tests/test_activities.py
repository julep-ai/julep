from uuid import uuid4

from ward import test

from agents_api.activities.embed_docs import embed_docs
from agents_api.activities.types import EmbedDocsPayload
from agents_api.clients import temporal
from agents_api.env import temporal_task_queue
from agents_api.workflows.demo import DemoWorkflow

from .fixtures import (
    cozo_client,
    patch_embed_acompletion,
    test_developer_id,
    test_doc,
)
from .utils import patch_testing_temporal

# from agents_api.activities.truncation import get_extra_entries
# from agents_api.autogen.openapi_model import Role
# from agents_api.common.protocol.entries import Entry


@test("activity: call direct embed_docs")
async def _(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    doc=test_doc,
    mocks=patch_embed_acompletion,
):
    (embed, _) = mocks

    title = "title"
    content = ["content 1"]
    include_title = True

    await embed_docs(
        EmbedDocsPayload(
            developer_id=developer_id,
            doc_id=doc.id,
            title=title,
            content=content,
            include_title=include_title,
            embed_instruction=None,
        ),
        cozo_client,
    )

    embed.assert_called_once()


@test("activity: call demo workflow via temporal client")
async def _():
    async with patch_testing_temporal() as (_, mock_get_client):
        client = await temporal.get_client()

        result = await client.execute_workflow(
            DemoWorkflow.run,
            args=[1, 2],
            id=str(uuid4()),
            task_queue=temporal_task_queue,
        )

        assert result == 3
        mock_get_client.assert_called_once()
