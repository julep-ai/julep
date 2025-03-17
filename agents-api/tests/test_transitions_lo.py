import json
from uuid import uuid4

from agents_api.autogen.openapi_model import CreateExecutionRequest
from agents_api.clients.pg import create_db_pool
from agents_api.common.utils.transitions_lo import (
    get_transition_output,
    store_transition_output,
    update_transition_output,
    bulk_get_transition_outputs,
)
from agents_api.queries.executions.create_execution import create_execution
from ward import test

from tests.fixtures import pg_dsn, test_developer_id, test_task


@test("transitions_lo: store and get transition output")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    pool = await create_db_pool(dsn=dsn)

    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
  
    # Create a test transition with output
    transition_id = uuid4()
    test_data = {"key": "value", "nested": {"field": 123}, "array": [1, 2, 3]}
    
    async with pool.acquire() as conn:
        # Store the output
        output_oid = await store_transition_output(conn, test_data)
        assert output_oid is not None
        
        # Insert a test transition record
        execution_id = execution.id
        await conn.execute(
            """
            INSERT INTO transitions 
            (execution_id, transition_id, type, current_step, output_oid)
            VALUES 
            ($1, $2, 'init', ROW('test', 1, $3), $4)
            """,
            execution_id, transition_id, uuid4(), output_oid
        )
        
        # Retrieve the output
        result = await get_transition_output(conn, transition_id)
        assert (result) == test_data


@test("transitions_lo: update transition output")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    pool = await create_db_pool(dsn=dsn)
    
    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    
    # Create a test transition with output
    transition_id = uuid4()
    initial_data = {"initial": "data"}
    updated_data = {"updated": "data", "with": "new fields"}
    
    async with pool.acquire() as conn:
        # Store the initial output
        output_oid = await store_transition_output(conn, initial_data)
        
        # Insert a test transition record
        execution_id = execution.id
        await conn.execute(
            """
            INSERT INTO transitions 
            (execution_id, transition_id, type, current_step, output_oid)
            VALUES 
            ($1, $2, 'init', ROW('test', 1, $3), $4)
            """,
            execution_id, transition_id, uuid4(), output_oid
        )
        
        # Verify initial data
        result = await get_transition_output(conn, transition_id)
        assert (result) == initial_data
        
        # Update the output
        await update_transition_output(conn, transition_id, updated_data)
        
        # Verify updated data
        updated_result = await get_transition_output(conn, transition_id)
        assert (updated_result) == updated_data


@test("transitions_lo: bulk get transition outputs")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    pool = await create_db_pool(dsn=dsn)
    
    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    
    # Create multiple test transitions
    transition_ids = [uuid4() for _ in range(3)]
    test_data = [
        {"id": 1, "name": "first"},
        {"id": 2, "name": "second"},
        {"id": 3, "name": "third"}
    ]
    
    async with pool.acquire() as conn:
        # Create an execution first for all transitions
        execution_id = execution.id
        
        # Store each output and create transition
        for i, (transition_id, data) in enumerate(zip(transition_ids, test_data)):
            output_oid = await store_transition_output(conn, data)
            
            # First transition needs to be 'init', others can be other terminal types
            transition_type = 'init' if i == 0 else 'step'
            
            await conn.execute(
                """
                INSERT INTO transitions 
                (execution_id, transition_id, type, current_step, output_oid)
                VALUES 
                ($1, $2, $3, ROW('test', $4, $5), $6)
                """,
                execution_id, transition_id, transition_type, i, uuid4(), output_oid
            )
        
        # Retrieve all outputs in bulk
        results = await bulk_get_transition_outputs(conn, transition_ids)
        
        # Verify all data was retrieved correctly
        assert len(results) == 3
        for transition_id, data in zip(transition_ids, test_data):
            assert results[transition_id] == data


@test("transitions_lo: large output data")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    pool = await create_db_pool(dsn=dsn)
    
    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
     
    # Create a test with large output data
    transition_id = uuid4()
    
    # Generate a larger dataset (~ 1MB)
    large_data = {
        "items": [{"id": i, "data": "x" * 1000} for i in range(1000)],
        "metadata": {"description": "Large test dataset"}
    }
    
    async with pool.acquire() as conn:
        # Store the large output
        output_oid = await store_transition_output(conn, large_data)
        
        # Insert a test transition record
        execution_id = execution.id
        await conn.execute(
            """
            INSERT INTO transitions 
            (execution_id, transition_id, type, current_step, output_oid)
            VALUES 
            ($1, $2, 'init', ROW('test', 1, $3), $4)
            """,
            execution_id, transition_id, uuid4(), output_oid
        )
        
        # Retrieve the output
        result = await get_transition_output(conn, transition_id)
        
        # Verify the data is retrieved correctly
        assert result["metadata"] == large_data["metadata"]
        assert len(result["items"]) == len(large_data["items"])
        
        # Check a sample item
        assert result["items"][42]["id"] == 42
        assert result["items"][42]["data"] == "x" * 1000