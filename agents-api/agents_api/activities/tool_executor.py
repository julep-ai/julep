import json
from typing import Any

from temporalio import activity

from ..autogen.openapi_model import (
    ToolExecutionResult,
    WebPreviewToolCall,
)
from ..clients.integrations import run_integration_service
from ..env import brave_api_key


async def execute_web_search_tool(tool_call: WebPreviewToolCall) -> ToolExecutionResult:
    """
    Execute a web search tool call using the Brave search integration.

    Args:
        tool_call: The web search tool call with query details

    Returns:
        ToolExecutionResult containing the search results
    """
    try:
        # Get the query from wherever it might be in the tool call
        query = tool_call.query

        if not query:
            return ToolExecutionResult(
                id=tool_call.id,
                output={},
                error="No search query found in the web search tool call",
            )

        # Map WebSearchTool to Brave search integration
        brave_args = {
            "query": query,
        }

        # Execute the Brave search integration
        # Note: Brave API key must be configured in environment variables
        result = await run_integration_service(
            provider="brave",
            setup={"brave_api_key": brave_api_key},
            arguments=brave_args,
            method="search",
        )

        # Convert result to BraveSearchOutput format
        search_results = [
            {
                "title": r.get("title", ""),
                "link": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            }
            for r in result.get("result", [])
        ]
        formatted_result = {"result": search_results}

        return ToolExecutionResult(
            id=tool_call.id, output=formatted_result, name=tool_call.name
        )
    except Exception as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_web_search_tool: {e}")
        raise


async def execute_tool_call(tool_call: dict[str, Any]) -> ToolExecutionResult:
    """
    Execute a single tool call based on its type and return the result.

    Args:
        tool_call: The tool call to execute (dict)

    Returns:
        ToolExecutionResult containing the output or error
    """
    # Initialize defaults
    tool_id = ""
    tool_name = None
    tool_type = ""

    try:
        tool_id = tool_call.get("id", "")
        tool_type = tool_call.get("type", "")

        # Get function name if present
        if "function" in tool_call and isinstance(tool_call["function"], dict):
            tool_name = tool_call["function"].get("name")

        # Handle web search tools
        if tool_type == "web_search_preview":
            # Extract query directly for web_search_preview type
            query = tool_call.get("query", "")

            web_search_call = WebPreviewToolCall(id=tool_id, query=query, name=tool_name)
            return await execute_web_search_tool(web_search_call)

        if tool_type == "function":
            # Extract function data
            func_data = tool_call.get("function", {})

            if not func_data:
                return ToolExecutionResult(
                    id=tool_id,
                    name=tool_name,
                    output={},
                    error="Function call missing function details",
                )

            # Extract function name if not already set
            if not tool_name:
                if isinstance(func_data, dict):
                    tool_name = func_data.get("name")
                else:
                    tool_name = getattr(func_data, "name", None)

            # Handle web search function
            if tool_name == "web_search_preview":
                # Parse arguments
                args = {}
                arguments_str = ""

                if isinstance(func_data, dict):
                    arguments_str = func_data.get("arguments", "")
                else:
                    arguments_str = getattr(func_data, "arguments", "")

                if arguments_str:
                    try:
                        args = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        raise

                # Get query from arguments
                query = args.get("query", "")
                if not query:
                    return ToolExecutionResult(
                        id=tool_id,
                        name=tool_name,
                        output={},
                        error="No search query found in the web search function call",
                    )

                web_search_call = WebPreviewToolCall(id=tool_id, query=query, name=tool_name)
                return await execute_web_search_tool(web_search_call)

        # Unsupported tool type
        return ToolExecutionResult(
            id=tool_id,
            name=tool_name,
            output={},
            error=f"Unsupported tool call type: {tool_type}",
        )

    except Exception as e:
        if activity.in_activity():
            tool_info = f"{tool_type}"
            if tool_name:
                tool_info += f".{tool_name}"
            activity.logger.error(f"Error in execute_tool_call {tool_info}: {e}")
        raise


def format_tool_results_for_llm(result: ToolExecutionResult) -> dict[str, Any]:
    """
    Format tool execution results into a structure suitable for sending back to the LLM.

    Args:
        result: Tool execution result

    Returns:
        Formatted tool result for the LLM
    """
    # Create base structure
    formatted_result = {
        "role": "tool",
        "tool_call_id": result.id,
        "name": result.name,
    }

    # Add content based on whether there was an error
    if result.error:
        formatted_result["content"] = json.dumps({"error": result.error})
    else:
        # Handle serialization with custom JSON encoder
        try:
            if isinstance(result.output, dict):
                formatted_result["content"] = json.dumps(result.output, default=lambda o: str(o))
            else:
                formatted_result["content"] = str(result.output)
        except Exception as e:
            formatted_result["content"] = json.dumps({"error": f"Failed to serialize tool output: {str(e)}"})

    return formatted_result
