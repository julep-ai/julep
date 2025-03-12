from typing import Any

from pydantic import BaseModel, ValidationError

from ...activities.task_steps.base_evaluate import validate_task_expressions
from ...autogen.openapi_model import CreateTaskRequest, PatchTaskRequest, UpdateTaskRequest
from ...common.protocol.models import task_to_spec


class ValidationIssue(BaseModel):
    """Represents a validation issue found in a task specification."""

    location: str
    message: str
    severity: str = "error"  # error, warning, info
    details: dict[str, Any] | None = None


class TaskValidationResult(BaseModel):
    """Result of task validation with issues categorized by type."""

    is_valid: bool
    python_expression_issues: list[ValidationIssue] = []
    schema_issues: list[ValidationIssue] = []
    other_issues: list[ValidationIssue] = []


def validate_task(
    task: CreateTaskRequest | UpdateTaskRequest | PatchTaskRequest,
) -> TaskValidationResult:
    """
    Validates a task spec for common issues before accepting it.

    Args:
        task: The task to validate (Create, Update, or Patch request)

    Returns:
        TaskValidationResult with validation issues
    """
    validation_result = TaskValidationResult(is_valid=True)

    # Convert to task spec (this will exclude version, developer_id etc.)
    try:
        task_spec = task_to_spec(task)
        task_spec_dict = task_spec.model_dump()

        # Validate Python expressions
        expression_results = validate_task_expressions(task_spec_dict)

        # Convert expression validation results to ValidationIssue objects
        for workflow_name, steps in expression_results.items():
            for step_idx, issues in steps.items():
                for issue in issues:
                    for issue_type, issue_messages in issue["issues"].items():
                        if not issue_messages:
                            continue

                        for message in issue_messages:
                            validation_result.python_expression_issues.append(
                                ValidationIssue(
                                    location=f"workflows.{workflow_name}.steps[{step_idx}].{issue['location']}",
                                    message=message,
                                    severity="error"
                                    if issue_type in ["syntax_errors", "undefined_names"]
                                    else "warning",
                                    details={
                                        "issue_type": issue_type,
                                        "expression": issue["expression"],
                                    },
                                )
                            )

    except ValidationError as e:
        # Handle Pydantic validation errors
        for error in e.errors():
            validation_result.schema_issues.append(
                ValidationIssue(
                    location=".".join(str(loc) for loc in error["loc"]),
                    message=error["msg"],
                    severity="error",
                    details={"error_type": error["type"]},
                )
            )

    except Exception as e:
        # Handle any other exceptions during validation
        validation_result.other_issues.append(
            ValidationIssue(
                location="task",
                message=f"Unexpected error during validation: {e!s}",
                severity="error",
            )
        )

    # Determine if the task is valid (no errors)
    has_errors = any(
        issue.severity == "error"
        for issues in [
            validation_result.python_expression_issues,
            validation_result.schema_issues,
            validation_result.other_issues,
        ]
        for issue in issues
    )

    validation_result.is_valid = not has_errors

    return validation_result
