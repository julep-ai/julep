from datetime import datetime, timezone
from uuid import uuid4

from ward import test

from agents_api.activities.utils import get_integration_arguments
from agents_api.autogen.Tools import DummyIntegrationDef, Tool


@test("get_integration_arguments: dummy search")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=DummyIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {},
        "required": [],
    }
