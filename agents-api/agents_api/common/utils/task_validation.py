import ast
from typing import Any

from pydantic import BaseModel, ValidationError

from ...autogen.openapi_model import CreateTaskRequest, PatchTaskRequest, UpdateTaskRequest
from ...common.protocol.models import task_to_spec
from ...env import enable_backwards_compatibility_for_syntax
from ...common.utils.evaluator import ALLOWED_FUNCTIONS, stdlib


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


def backwards_compatibility(expr: str) -> str:
    """
    Convert expressions to a consistent format for evaluation.

    Args:
        expr: The expression to convert

    Returns:
        The converted expression with $ prefix where appropriate
    """
    # Note: This function returns expressions that start with "$ "
    # The space after $ is required for expressions to be evaluated as Python code.

    expr = expr.strip()

    # Check if it already starts with $ followed by a space
    if expr.startswith("$ "):
        return expr

    if "{{" in expr:
        return "$ f'''" + expr.replace("{{", "{").replace("}}", "}") + "'''"

    if (
        (expr.startswith("[") and expr.endswith("]"))
        or (expr.startswith("_[") and expr.endswith("]"))
        or expr.startswith("_.")
        or "outputs[" in expr
        or "inputs[" in expr
        or expr == "_"
    ):
        return "$ " + expr  # Keep space after $ for backward compatibility

    return expr


# Build the set of allowed names
allowed_names = (
    set(ALLOWED_FUNCTIONS.keys())
    | set(stdlib.keys())
    | {"true", "false", "null", "NEWLINE", "hasattr"}  # helpers
    | {"_", "inputs", "outputs", "state", "steps"}  # Special vars
)


def validate_py_expression(
    expr: str | None,
    expected_variables: set[str] | None = None,
) -> dict[str, list[str]]:
    """
    Statically validate a Python expression before task execution.

    Args:
        expr: The Python expression to validate (or None)
        expected_variables: Optional set of expected variable names that should be available

    Returns:
        Dict with potential issues categorized by type
    """
    issues: dict[str, list[str]] = {
        "syntax_errors": [],
        "undefined_names": [],
        "unsafe_operations": [],
        "potential_runtime_errors": [],
        "unsupported_features": [],
    }

    # Skip None or empty expressions
    if expr is None or not expr:
        return issues

    # Ensure the expression is stripped before checking prefix
    expr = expr.strip()

    # Apply backwards compatibility transformation first
    if enable_backwards_compatibility_for_syntax:
        expr = backwards_compatibility(expr)

    # The space after $ is required for expressions to be evaluated as Python code
    if not expr.startswith("$ "):
        return issues

    # Remove $ and strip any leading space after $
    expr = expr[1:].lstrip()

    # Special case: just a $ sign with nothing after it
    if not expr:
        return issues

    # Try to parse the expression to check for syntax errors
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        issues["syntax_errors"].append(f"Syntax error: {e!s}")
        return issues  # Return early if we can't even parse the expression

    expected_variables: set[str] = expected_variables or set()

    # Track locally defined variables to avoid flagging them as undefined
    local_vars: set[str] = set()

    # NOTE: if we update the evaluator to support these features, we can remove the 3 checks below
    # Check for unsupported language features
    for node in ast.walk(tree):
        # Check for set comprehensions
        if isinstance(node, ast.SetComp):
            issues["unsupported_features"].append(
                "Set comprehensions are not supported in this evaluator"
            )

        # Check for lambda functions
        elif isinstance(node, ast.Lambda):
            issues["unsupported_features"].append(
                "Lambda functions are not supported in this evaluator"
            )

        # Check for assignment expressions (walrus operator)
        elif isinstance(node, ast.NamedExpr):
            issues["unsupported_features"].append(
                "Assignment expressions (walrus operator) are not supported in this evaluator"
            )

    # Find all comprehension variables and other locally defined variables
    for node in ast.walk(tree):
        # List, dict, and set comprehensions
        if isinstance(node, ast.ListComp | ast.DictComp | ast.SetComp):
            for generator in node.generators:
                # Add target names from comprehensions
                if isinstance(generator.target, ast.Name):
                    local_vars.add(generator.target.id)
                elif isinstance(generator.target, ast.Tuple):
                    for elt in generator.target.elts:
                        if isinstance(elt, ast.Name):
                            local_vars.add(elt.id)

        # Generator expressions
        elif isinstance(node, ast.GeneratorExp):
            for generator in node.generators:
                if isinstance(generator.target, ast.Name):
                    local_vars.add(generator.target.id)
                elif isinstance(generator.target, ast.Tuple):
                    for elt in generator.target.elts:
                        if isinstance(elt, ast.Name):
                            local_vars.add(elt.id)

        # Lambda functions
        elif isinstance(node, ast.Lambda):
            for arg in node.args.args:
                local_vars.add(arg.arg)

            # Handle args with default values
            if node.args.kwonlyargs:
                for arg in node.args.kwonlyargs:
                    local_vars.add(arg.arg)

        # Assignment expressions (walrus operator)
        elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
            local_vars.add(node.target.id)

    # Get all name references in the expression
    name_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Name)]

    # Check for undefined names
    referenced_names = {
        node.id
        for node in name_nodes
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }

    # Find undefined names, excluding locally defined variables
    undefined_names = referenced_names - allowed_names - expected_variables - local_vars
    if undefined_names:
        issues["undefined_names"].extend([
            f"Undefined name: '{name}'" for name in undefined_names
        ])

    # Check for potentially unsafe operations
    for node in ast.walk(tree):
        # Check for attribute access that might be unsafe
        if isinstance(node, ast.Attribute):
            # Allow specific attributes on known objects
            attr_name = node.attr

            # Check for dunder attributes which are potentially dangerous
            if attr_name.startswith("__") and attr_name.endswith("__"):
                issues["unsafe_operations"].append(
                    f"Potentially unsafe dunder attribute access: {attr_name}"
                )
                continue

            if isinstance(node.value, ast.Name):
                obj_name = node.value.id

                # Allow accessing attributes on allowed names
                if obj_name in (expected_variables | allowed_names):
                    continue

                # Otherwise flag unexpected attribute access
                issues["unsafe_operations"].append(
                    f"Potentially unsafe attribute access: {obj_name}.{attr_name}"
                )

        # Check for function calls to make sure they're allowed
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name not in (expected_variables | allowed_names):
                issues["unsafe_operations"].append(
                    f"Call to potentially unsafe function: {func_name}"
                )

    # Check for common potential runtime errors
    for node in ast.walk(tree):
        # Division by zero
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and isinstance(node.right, ast.Constant)
            and node.right.value == 0
        ):
            issues["potential_runtime_errors"].append("Division by zero detected")

        # Index out of bounds for list literals
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.List)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, int)
        ):
            list_size = len(node.value.elts)
            index = node.slice.value
            if index >= list_size:
                issues["potential_runtime_errors"].append(
                    f"Possible index error: index {index} exceeds list size {list_size}"
                )

    return issues


def _validate_step_expressions(
    step: dict[str, Any],
    location_prefix: str = "",
) -> list[dict[str, Any]]:
    """
    Recursively validate expressions in a single step or nested step structure.

    Args:
        step: The step dictionary to validate
        location_prefix: String prefix to prepend to location path for nested steps

    Returns:
        List of validation issues found in this step and its nested components
    """
    step_issues = []

    # Identify which step type we're dealing with
    step_type = step.get("kind_")
    step_data = {}

    # If kind_ field is present, use it to determine step type
    if step_type:
        # Handle special case for if_else step (converted from "if" in the original task)
        if step_type == "if_else":
            step_data = {
                "if_": step.get("if_"),
                "then": step.get("then"),
                "else_": step.get("else_"),
            }
        else:
            # For other steps, find the data dict by the same name as kind_
            for key, value in step.items():
                if key == step_type and isinstance(value, dict):
                    step_data = value
                    break
    else:
        # Fall back to the old method if kind_ is not present
        for key, value in step.items():
            if key not in ["id", "name", "label"] and isinstance(value, dict):
                step_type = key
                step_data = value
                break

    if not step_type or not step_data:
        return step_issues

    # Add location prefix if provided
    loc_prefix = f"{location_prefix}." if location_prefix else ""

    # Check for Python expressions based on step type
    if step_type == "evaluate":
        # In evaluate steps, all values are potentially expressions
        for eval_key, eval_value in step_data.items():
            if isinstance(eval_value, str) and (
                eval_value.strip().startswith(("$", "_"))
                or "{{" in eval_value
                or eval_value.strip() == "_"
            ):
                issues = validate_py_expression(eval_value)
                if any(issues.values()):  # If we found any issues
                    step_issues.append({
                        "location": f"{loc_prefix}{step_type}.{eval_key}",
                        "expression": eval_value,
                        "issues": issues,
                    })

    elif step_type == "if":
        # For "if" steps, the condition is the value of the "if" key itself
        condition = step.get(step_type)
        if isinstance(condition, str):
            issues = validate_py_expression(condition)
            if any(issues.values()):
                step_issues.append({
                    "location": f"{loc_prefix}{step_type}",
                    "expression": condition,
                    "issues": issues,
                })

        # Check "then" and "else" branches for expressions
        for branch in ["then", "else"]:
            if branch in step_data and isinstance(step_data[branch], dict):
                # Recursively validate the nested step
                nested_step = step_data[branch]
                nested_location = f"{loc_prefix}{step_type}.{branch}"
                nested_issues = _validate_step_expressions(nested_step, nested_location)
                step_issues.extend(nested_issues)

    elif step_type == "if_else":
        # For if_else steps, check the condition in if_ field
        if "if_" in step_data and isinstance(step_data["if_"], str):
            issues = validate_py_expression(step_data["if_"])
            if any(issues.values()):
                step_issues.append({
                    "location": f"{loc_prefix}{step_type}.if",
                    "expression": step_data["if_"],
                    "issues": issues,
                })

        # Check then and else branches
        for branch, key in [("then", "then"), ("else", "else_")]:
            if key in step_data and isinstance(step_data[key], dict):
                nested_step = step_data[key]
                nested_location = f"{loc_prefix}{step_type}.{branch}"
                nested_issues = _validate_step_expressions(nested_step, nested_location)
                step_issues.extend(nested_issues)

    elif step_type == "match":
        # Check condition expression for match statements
        if "case" in step_data and isinstance(step_data["case"], str):
            issues = validate_py_expression(step_data["case"])
            if any(issues.values()):
                step_issues.append({
                    "location": f"{loc_prefix}{step_type}.case",
                    "expression": step_data["case"],
                    "issues": issues,
                })

        # For match statements, check all cases in "cases" array
        if "cases" in step_data and isinstance(step_data["cases"], list):
            for case_idx, case_item in enumerate(step_data["cases"]):
                if (
                    "case" in case_item
                    and isinstance(case_item["case"], str)
                    and case_item["case"] != "_"
                ):
                    issues = validate_py_expression(case_item["case"])
                    if any(issues.values()):
                        step_issues.append({
                            "location": f"{loc_prefix}{step_type}.cases[{case_idx}].case",
                            "expression": case_item["case"],
                            "issues": issues,
                        })

                # Check for nested structure inside each case's "then" field
                if "then" in case_item and isinstance(case_item["then"], dict):
                    nested_step = case_item["then"]
                    nested_location = f"{loc_prefix}{step_type}.cases[{case_idx}].then"
                    nested_issues = _validate_step_expressions(nested_step, nested_location)
                    step_issues.extend(nested_issues)

    elif step_type in ["foreach", "map"]:
        # Check "in" expression for iterable
        if "in" in step_data and isinstance(step_data["in"], str):
            issues = validate_py_expression(step_data["in"])
            if any(issues.values()):
                step_issues.append({
                    "location": f"{loc_prefix}{step_type}.in",
                    "expression": step_data["in"],
                    "issues": issues,
                })

        # Check for nested structure in do field
        if "do" in step_data and isinstance(step_data["do"], dict):
            nested_step = step_data["do"]
            nested_location = f"{loc_prefix}{step_type}.do"
            nested_issues = _validate_step_expressions(nested_step, nested_location)
            step_issues.extend(nested_issues)

    elif step_type == "tool" and "arguments" in step_data:
        # Check arguments that might be expressions
        for arg_key, arg_value in step_data["arguments"].items():
            if isinstance(arg_value, str) and (
                arg_value.strip().startswith(("$", "_"))
                or "{{" in arg_value
                or arg_value.strip() == "_"
            ):
                issues = validate_py_expression(arg_value)
                if any(issues.values()):
                    step_issues.append({
                        "location": f"{loc_prefix}{step_type}.arguments.{arg_key}",
                        "expression": arg_value,
                        "issues": issues,
                    })

    # Also recursively validate any other string values that could be expressions
    for key, value in step_data.items():
        if (
            isinstance(value, str)
            and (value.strip().startswith(("$", "_")) or "{{" in value or value.strip() == "_")
            and key not in ["if_", "case"]
        ):  # Skip keys we've already checked
            issues = validate_py_expression(value)
            if any(issues.values()):
                step_issues.append({
                    "location": f"{loc_prefix}{step_type}.{key}",
                    "expression": value,
                    "issues": issues,
                })

    return step_issues


def validate_task_expressions(
    task_spec: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """
    Validate all Python expressions in a task specification.

    Args:
        task_spec: The task specification dictionary

    Returns:
        Dict mapping workflow names to step indices to lists of expression validation issues
    """
    validation_results: dict[str, dict[str, list[dict[str, Any]]]] = {}

    # Process all workflows in the task
    if "workflows" not in task_spec:
        return validation_results

    for workflow in task_spec.get("workflows", []):
        workflow_name = workflow.get("name", "unknown")
        validation_results[workflow_name] = {}

        for step_idx, step in enumerate(workflow.get("steps", [])):
            step_issues = _validate_step_expressions(step)

            # Store issues for this step if we found any
            if step_issues:
                validation_results[workflow_name][str(step_idx)] = step_issues

    return validation_results


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
                                    if issue_type
                                    in [
                                        "syntax_errors",
                                        "undefined_names",
                                        "unsupported_features",
                                    ]
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
