from uuid import uuid4

from ward import test

from agents_api.activities.embed_docs import embed_docs
from agents_api.activities.types import EmbedDocsPayload
from agents_api.clients import temporal
from agents_api.env import temporal_task_queue
from agents_api.workflows.demo import DemoWorkflow
from agents_api.workflows.task_execution.helpers import DEFAULT_RETRY_POLICY

from .fixtures import (
    cozo_client,
    test_developer_id,
    test_doc,
)
from .utils import patch_testing_temporal


@test("activity: call direct embed_docs")
async def _(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    doc=test_doc,
):
    title = "title"
    content = ["content 1"]
    include_title = True

    # QUESTION[@Bhabuk10]: Why is the `include_title` flag set to True in this test case? 
    # Is there a scenario where embedding behavior would change based on this flag's value? 
    # It may be useful to add a test case that explicitly verifies this.

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

    # FEEDBACK[@Bhabuk10]: It would be beneficial to include assertions here that verify the 
    # expected outcome after calling `embed_docs`. This could be checking that the document was 
    # embedded correctly or validating the result in some way to ensure that the function works as intended.

@test("activity: call demo workflow via temporal client")
async def _():
    async with patch_testing_temporal() as (_, mock_get_client):
        client = await temporal.get_client()

        result = await client.execute_workflow(
            DemoWorkflow.run,
            args=[1, 2],
            id=str(uuid4()),
            task_queue=temporal_task_queue,
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        assert result == 3

        # FEEDBACK[@Bhabuk10]: Consider adding a comment explaining why the expected result is 3. 
        # Including a brief description of how `DemoWorkflow` works can make the test more understandable to others.

        mock_get_client.assert_called_once()

        # FEEDBACK[@Bhabuk10]: Good practice in verifying that the temporal client was called once. 
        # You may also want to test edge cases like invalid input arguments or failure scenarios to 
        # increase the coverage of the test suite.
