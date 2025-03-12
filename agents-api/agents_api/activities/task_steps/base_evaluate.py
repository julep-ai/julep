import ast
from typing import Any

import simpleeval
from beartype import beartype
from box import Box
from openai import BaseModel

# Increase the max string length to 2048000
simpleeval.MAX_STRING_LENGTH = 2048000

from simpleeval import SimpleEval
from temporalio import activity

from ...common.exceptions.executions import EvaluateError
from ...common.protocol.tasks import StepContext
from ..utils import ALLOWED_FUNCTIONS, get_evaluator, stdlib


def backwards_compatibility(expr: str) -> str:
    expr = expr.strip()

    # Check if it already starts with $ (with or without space)
    if expr.startswith("$"):
        return expr

    if "{{" in expr:
        return "$ f'''" + expr.replace("{{", "{").replace("}}", "}") + "'''"

    if (
        (expr.startswith("[") and expr.endswith("]"))
        or (expr.startswith("_[") and expr.endswith("]"))
        or (expr.startswith("_.") and expr.endswith("]"))
        or "outputs[" in expr
        or "inputs[" in expr
        or expr == "_"
    ):
        return "$ " + expr  # Keep space after $ for backward compatibility

    return expr


# Recursive evaluation helper function
def _recursive_evaluate(expr, evaluator: SimpleEval):
    # Handle PyExpression type from the model
    if hasattr(expr, "root") and isinstance(expr.root, str):
        # Extract the string from the RootModel
        expr = expr.root

    if isinstance(expr, str):
        try:
            expr = backwards_compatibility(expr)
            expr = expr.strip()
            if isinstance(expr, str) and expr.startswith("$"):
                # Remove $ and any space after it
                expr = expr[1:].strip()
            else:
                expr = f"f'''{expr}'''"
            return evaluator.eval(expr)
        except Exception as e:
            evaluate_error = EvaluateError(e, expr, evaluator.names)
            if activity.in_activity():
                activity.logger.error(f"Error in base_evaluate: {evaluate_error}\n")
            raise evaluate_error from e
    elif isinstance(expr, int | bool | float):
        return expr
    elif isinstance(expr, list):
        return [_recursive_evaluate(e, evaluator) for e in expr]
    elif isinstance(expr, dict):
        return {k: _recursive_evaluate(v, evaluator) for k, v in expr.items()}
    else:
        msg = f"Invalid expression: {expr}"
        raise ValueError(msg)


@activity.defn
@beartype
async def base_evaluate(
    exprs: Any,
    context: StepContext | None = None,
    values: dict[str, Any] | None = None,
    extra_lambda_strs: dict[str, str] | None = None,
) -> Any | list[Any] | dict[str, Any]:
    if context is None and values is None:
        msg = "Either context or values must be provided"
        raise ValueError(msg)

    values = values or {}
    if context:
        values.update(await context.prepare_for_step())

    # Handle PyExpression objects and strings similarly
    if isinstance(exprs, str) or (hasattr(exprs, "root") and isinstance(exprs.root, str)):
        input_len = 1
    else:
        input_len = len(exprs)

    assert input_len > 0, "exprs must be a non-empty string, PyExpression, list or dict"

    extra_lambdas = {}
    if extra_lambda_strs:
        for k, v in extra_lambda_strs.items():
            v = v.strip()

            # Check that all extra lambdas are valid
            assert v.startswith("lambda "), "All extra lambdas must start with 'lambda'"

            try:
                ast.parse(v)
            except Exception as e:
                msg = f"Invalid lambda: {v}"
                raise ValueError(msg) from e

            # Eval the lambda and add it to the extra lambdas
            extra_lambdas[k] = eval(v)

    # Turn the nested dict values from pydantic to dicts where possible
    values = {k: v.model_dump() if isinstance(v, BaseModel) else v for k, v in values.items()}

    # frozen_box doesn't work coz we need some mutability in the values
    values = Box(values, frozen_box=False, conversion_box=True)

    evaluator: SimpleEval = get_evaluator(names=values, extra_functions=extra_lambdas)

    # Recursively evaluate the expression
    return _recursive_evaluate(exprs, evaluator)


def validate_py_expression(
    expr: str | None,
    allow_placeholder_variables: bool = True,
    expected_variables: set[str] | None = None,
) -> dict[str, list[str]]:
    """
    Statically validate a Python expression before task execution.

    Args:
        expr: The Python expression to validate (or None)
        allow_placeholder_variables: Whether to allow _ and placeholders like _.attr in expression
        expected_variables: Optional set of expected variable names that should be available

    Returns:
        Dict with potential issues categorized by type
    """
    issues: dict[str, list[str]] = {
        "syntax_errors": [],
        "undefined_names": [],
        "unsafe_operations": [],
        "potential_runtime_errors": [],
    }

    # Skip None or empty expressions
    if expr is None or not expr or not expr.strip():
        return issues

    # Apply backwards compatibility transformation first
    expr = backwards_compatibility(expr)

    # Ensure the expression is stripped before checking prefix
    expr = expr.strip()

    # Handle expressions with $ prefix - return early if it doesn't start with $
    if not expr.startswith("$"):
        return issues

    # Remove $ and strip any leading space after $
    expr = expr[1:].strip()

    # Special case: just a $ sign with nothing after it
    if not expr:
        return issues

    # Handle f-string expressions (these are often used in templates)
    if expr.startswith(("f'''", 'f"""')):
        # Just basic syntax check for f-strings, can't do much static analysis
        try:
            ast.parse(expr)
        except SyntaxError as e:
            issues["syntax_errors"].append(f"F-string syntax error: {e!s}")
        return issues

    # Try to parse the expression to check for syntax errors
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        issues["syntax_errors"].append(f"Syntax error: {e!s}")
        return issues  # Return early if we can't even parse the expression

    # Get all name references in the expression
    name_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Name)]

    # Check for undefined names
    referenced_names = {
        node.id
        for node in name_nodes
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }

    # Build the set of allowed names
    allowed_names = (
        set(ALLOWED_FUNCTIONS.keys())
        | set(stdlib.keys())
        | {"true", "false", "null", "NEWLINE", "hasattr"}
    )

    # Add standard placeholder variable names if allowed
    if allow_placeholder_variables:
        allowed_names.add("_")  # Special underscore variable
        # Some common inputs that might be accessed via _
        allowed_names.update({"inputs", "outputs", "state"})

    # Add expected variables if provided
    if expected_variables:
        allowed_names.update(expected_variables)

    # Find undefined names
    undefined_names = referenced_names - allowed_names
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
            if isinstance(node.value, ast.Name):
                obj_name = node.value.id

                # Allow accessing attributes on the underscore variable
                if obj_name == "_" and allow_placeholder_variables:
                    continue

                # Allow accessing attributes on stdlib modules
                if obj_name in stdlib:
                    continue

                # Allow accessing attributes on allowed names
                if obj_name in allowed_names:
                    continue

                # Otherwise flag unexpected attribute access
                issues["unsafe_operations"].append(
                    f"Potentially unsafe attribute access: {obj_name}.{attr_name}"
                )

        # Check for function calls to make sure they're allowed
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name not in ALLOWED_FUNCTIONS and func_name not in allowed_names:
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
            step_issues = []

            # Identify which step type we're dealing with
            # IMPORTANT: Steps can be represented in two ways:
            # 1. As Pydantic model objects with kind_ field (after passing through task_to_spec)
            # 2. As raw dictionaries with step type as the key (in original task JSON)
            # We need to handle both cases, with preference for kind_ field which is more reliable

            step_type = step.get("kind_")
            step_data = {}

            # If kind_ field is present, use it to determine step type
            if step_type:
                # Handle special case for if_else step (converted from "if" in the original task)
                # The if_else step has the condition in if_ field (with alias "if")
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
                # This handles raw dictionary representation where step type is the key
                for key, value in step.items():
                    if key not in ["id", "name", "label"] and isinstance(value, dict):
                        step_type = key
                        step_data = value
                        break

            if not step_type or not step_data:
                continue

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
                                "location": f"{step_type}.{eval_key}",
                                "expression": eval_value,
                                "issues": issues,
                            })

            elif step_type == "if":
                # For "if" steps, the condition is the value of the "if" key itself
                # Get the condition from step_type (the "if" key)
                condition = step.get(step_type)
                if isinstance(condition, str):
                    issues = validate_py_expression(condition)
                    if any(issues.values()):
                        step_issues.append({
                            "location": step_type,
                            "expression": condition,
                            "issues": issues,
                        })

                # Check "then" and "else" branches for expressions
                for branch in ["then", "else"]:
                    if branch in step_data and isinstance(step_data[branch], dict):
                        # Recursively process the nested step
                        # This is a simplified approach - for full validation, we'd need to process nested steps completely
                        pass

            elif step_type == "if_else":
                # For if_else steps, check the condition in if_ field
                # NOTE: The if_else step type comes from the Pydantic model conversion
                # In the original task JSON, this is an "if" step with the condition directly
                # in the "if" key. The task_to_spec function converts it to if_else with if_ field
                # (with alias "if") to avoid Python keyword conflicts.
                if "if_" in step_data and isinstance(step_data["if_"], str):
                    issues = validate_py_expression(step_data["if_"])
                    if any(issues.values()):
                        step_issues.append({
                            "location": f"{step_type}.if",
                            "expression": step_data["if_"],
                            "issues": issues,
                        })

            elif step_type == "match":
                # Check condition expression for match statements
                if "case" in step_data and isinstance(step_data["case"], str):
                    issues = validate_py_expression(step_data["case"])
                    if any(issues.values()):
                        step_issues.append({
                            "location": f"{step_type}.case",
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
                                    "location": f"{step_type}.cases[{case_idx}].case",
                                    "expression": case_item["case"],
                                    "issues": issues,
                                })

            elif step_type in ["foreach", "map"]:
                # Check "in" expression for iterable
                if "in" in step_data and isinstance(step_data["in"], str):
                    issues = validate_py_expression(step_data["in"])
                    if any(issues.values()):
                        step_issues.append({
                            "location": f"{step_type}.in",
                            "expression": step_data["in"],
                            "issues": issues,
                        })

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
                                "location": f"{step_type}.arguments.{arg_key}",
                                "expression": arg_value,
                                "issues": issues,
                            })

            # Store issues for this step if we found any
            if step_issues:
                validation_results[workflow_name][str(step_idx)] = step_issues

    return validation_results
