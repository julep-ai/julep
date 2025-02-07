from ...autogen.openapi_model import Transition


def get_workflow_name(transition: Transition) -> str:
    workflow_str = transition.current.workflow
    if workflow_str.startswith("PAR:`"):
        # Extract between PAR:` and first ` after "workflow"
        assert len(workflow_str) > 5 and "`" in workflow_str[5:], (
            "Workflow string is too short or missing backtick"
        )
        workflow_str = workflow_str[5:].split("`")[0]
    elif workflow_str.startswith("`"):
        # Extract between backticks
        assert len(workflow_str) > 1 and "`" in workflow_str[1:], (
            "Workflow string is too short or missing backtick"
        )
        workflow_str = workflow_str[1:].split("`")[0]
    return workflow_str
