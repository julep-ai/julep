# AIDEV-NOTE: Workflow name parsing utility for extracting base workflow from transition strings.
from ...autogen.openapi_model import Transition

PAR_PREFIX = "PAR:"
SEPARATOR = "`"


def get_workflow_name(transition: Transition) -> str:
    workflow_str = transition.current.workflow
    if workflow_str.startswith(PAR_PREFIX):
        # Extract between PAR:` and first ` after "workflow"
        start_index = len(PAR_PREFIX) + len(SEPARATOR)
        assert len(workflow_str) > start_index and SEPARATOR in workflow_str[start_index:], (
            "Workflow string is too short or missing backtick"
        )
        workflow_str = workflow_str[start_index:].split(SEPARATOR)[0]
    elif workflow_str.startswith(SEPARATOR):
        # Extract between backticks
        start_index = len(SEPARATOR)
        assert len(workflow_str) > start_index and SEPARATOR in workflow_str[start_index:], (
            "Workflow string is too short or missing backtick"
        )
        workflow_str = workflow_str[start_index:].split(SEPARATOR)[0]

    return workflow_str
