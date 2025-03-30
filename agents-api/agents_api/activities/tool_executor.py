import json
from typing import Any

import numpy as np
from beartype import beartype
from temporalio import activity

from ..autogen.openapi_model import (
    DocReference,
    FileToolCall,
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    ToolExecutionResult,
    WebPreviewToolCall,
)
from ..clients import litellm
from ..clients.integrations import run_integration_service
from ..common.utils.get_doc_search import get_search_fn_and_params
from ..common.utils.mmr import apply_mmr_to_docs
from ..env import brave_api_key


@beartype
async def execute_file_search_tool(tool_call: FileToolCall) -> ToolExecutionResult:
    """
    Execute a file search tool call using the FileSearchTool integration.

    Args:
        tool_call: The file search tool call with query details

    Returns:
        ToolExecutionResult containing the search results
    """
    try:
        # Get the query from wherever it might be in the tool call
        query = tool_call.query

        [query_embedding, *_] = await litellm.aembedding(
            inputs=query,
            embed_instruction="Represent the query for retrieving supporting documents: ",
        )

        # Get owners to search docs from
        owners = [("user", user) for user in tool_call.vector_store_ids]

        # set the MMR strength to 0.5 if the ranker is turned on
        mmr_strength = 0.5 if tool_call.ranker == "auto" else 0.0

        # Build search params based on mode
        search_params = HybridDocSearchRequest(
            lang="en-US",
            limit=tool_call.max_num_results,
            metadata_filter=tool_call.filters,
            confidence=tool_call.score_threshold,
            mmr_strength=mmr_strength,
            text=query,
            vector=query_embedding,
        )

        # Execute search (extract keywords for FTS because the query is a conversation snippet)
        extract_keywords: bool = True
        search_fn, params = get_search_fn_and_params(
            search_params, extract_keywords=extract_keywords
        )

        doc_references: list[DocReference] = await search_fn(
            developer_id=tool_call.developer_id,
            owners=owners,
            connection_pool=None,
            **params,
        )

        # Apply MMR if enabled and applicable
        if (
            not isinstance(search_params, TextOnlyDocSearchRequest)
            and len(doc_references) > tool_call.max_num_results
            and mmr_strength > 0
        ):
            doc_references = apply_mmr_to_docs(
                docs=doc_references,
                query_embedding=np.asarray(query_embedding),
                limit=tool_call.max_num_results or None,
                mmr_strength=mmr_strength,
            )

        # Convert result to DocReference format
        search_results = [
            {
                "title": doc.title,
                "id": doc.id,
                "content": doc.snippet.content,
                "distance": doc.distance,
                "metadata": doc.metadata,
                "owner": doc.owner.id,
                "role": doc.owner.role,
            }
            for doc in doc_references
        ]
        formatted_result = {"result": search_results}

        return ToolExecutionResult(
            id=tool_call.id, output=formatted_result, name=tool_call.name
        )
    except Exception as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_file_search_tool: {e}")
        raise


@beartype
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


@beartype
async def execute_tool_call(tool_call: dict[str, Any], **kwargs: Any) -> ToolExecutionResult:
    """
    Execute a single tool call based on its type and return the result.

    Args:
        tool_call: The tool call to execute (dict)
        **kwargs: Any additional arguments including user file_search_params
    Returns:
        ToolExecutionResult containing the output or error
    """
    # Initialize defaults
    tool_id: str = ""
    tool_name: str | None = None
    tool_type: str = ""

    try:
        tool_id = tool_call.get("id", "")
        tool_type = tool_call.get("type", "")

        # Get function name if present
        if "function" in tool_call and isinstance(tool_call["function"], dict):
            tool_name = tool_call["function"].get("name")

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
                args: dict[str, Any] = {}
                arguments_str: str = ""

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

            if tool_name == "file_search":
                # Check if user-provided parameters are available
                user_params = kwargs.get("user_tool_params", {}).get("file_search_params", {})
                # Fall back to parsing arguments if no user parameters
                args: dict[str, Any] = {}
                arguments_str: str = ""

                if isinstance(func_data, dict):
                    arguments_str = func_data.get("arguments", "")
                else:
                    arguments_str = getattr(func_data, "arguments", "")

                if arguments_str:
                    try:
                        args = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        return ToolExecutionResult(
                            id=tool_id,
                            name=tool_name,
                            output={},
                            error="Invalid JSON in file search arguments",
                        )

                # Extract parameters from arguments
                query = args.get("query", "")
                if not query:
                    return ToolExecutionResult(
                        id=tool_id,
                        name=tool_name,
                        output={},
                        error="No query provided for file search",
                    )
                filters = user_params.get("filters", None)
                max_num_results = user_params.get("max_num_results", None)
                ranking_options = user_params.get("ranking_options", {})
                ranker = ranking_options.get("ranker", "auto")
                score_threshold = ranking_options.get("score_threshold", None)
                vector_store_ids = user_params.get("vector_store_ids", [])

                if not vector_store_ids:
                    return ToolExecutionResult(
                        id=tool_id,
                        name=tool_name,
                        output={},
                        error="vector_store_ids cannot be empty for file search",
                    )

                # Create FileToolCall object with parameters
                file_search_call = FileToolCall(
                    id=tool_id,
                    developer_id=kwargs.get("developer_id"),
                    name=tool_name,
                    query=query,
                    filters=filters,
                    max_num_results=max_num_results,
                    ranker=ranker,
                    score_threshold=score_threshold,
                    vector_store_ids=vector_store_ids,
                )

                return await execute_file_search_tool(file_search_call)

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


@beartype
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
        formatted_result["content"] = (
            json.dumps(result.output) if isinstance(result.output, dict) else str(result.output)
        )

    return formatted_result
