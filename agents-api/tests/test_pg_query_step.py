from unittest.mock import AsyncMock, MagicMock, patch

from agents_api.activities.pg_query_step import pg_query_step
from ward import skip, test


@test("pg_query_step correctly calls the specified query")
async def _():
    # Patch the relevant modules and functions
    with (
        patch("agents_api.activities.pg_query_step.queries") as mock_queries,
    ):
        # Create a mock query function that will be returned by getattr
        mock_query = AsyncMock(return_value={"result": "test"})

        # Set up module resolution chain: queries -> test_module -> test_file -> test_query
        mock_test_file = MagicMock()
        mock_test_file.test_query = mock_query
        
        mock_test_module = MagicMock()
        mock_test_module.test_file = mock_test_file
        
        # Configure the queries module to return our mock module
        mock_queries.test_module = mock_test_module

        # Call the function with a query in the format "module_name.query_name"
        result = await pg_query_step(
            query_name="test_query",
            file_name="test_module.test_file",
            values={"param1": "value1"},
        )

        # Verify the query was called with the expected arguments
        mock_query.assert_called_once_with(param1="value1")

        # Verify the function returns the result from the query
        assert result == {"result": "test"}


@test("pg_query_step raises exception for invalid query name format")
async def _():
    # Try with an invalid query name (no dot separator)
    try:
        await pg_query_step(query_name="invalid_query_name", file_name="invalid_file_name", values={})
        assert False, "Expected an exception but none was raised"
    except ValueError:
        # Expected behavior - ValueError should be raised
        pass
    except Exception as e:
        assert False, f"Expected ValueError but got {type(e).__name__}"


@test("pg_query_step propagates exceptions from the underlying query")
async def _():
    # Patch the relevant modules and functions
    with patch("agents_api.activities.pg_query_step.queries") as mock_queries:
        # Create a mock query function that raises an exception
        mock_query = AsyncMock(side_effect=Exception("Test query error"))

        # Set up module resolution chain: queries -> test_module -> test_file -> test_query
        mock_test_file = MagicMock()
        mock_test_file.test_query = mock_query
        
        mock_test_module = MagicMock()
        mock_test_module.test_file = mock_test_file
        
        # Configure the queries module to return our mock module
        mock_queries.test_module = mock_test_module

        # Call the function and expect an exception
        try:
            await pg_query_step(
                query_name="test_query",
                file_name="test_module.test_file",
                values={},
            )
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            # Verify the exception is propagated
            assert str(e) == "Test query error"
