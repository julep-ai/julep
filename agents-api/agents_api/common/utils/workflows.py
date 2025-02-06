from ...autogen.openapi_model import Transition


def get_workflow_name(transition: Transition) -> str:
    workflow_str = transition.current.workflow
    if workflow_str.startswith("PAR:`"):
        # Extract between PAR:` and first ` after "workflow"
        workflow_str = workflow_str[6:].split("`")[0]
    elif workflow_str.startswith("`"):
        # Extract between backticks
        workflow_str = workflow_str[1:].split("`")[0]
    return workflow_str
