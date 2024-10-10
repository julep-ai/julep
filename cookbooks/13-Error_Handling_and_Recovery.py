# Error Handling and Recovery Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for error handling demonstration
# 3. Define a task with potential errors and recovery mechanisms
# 4. Execute the task and demonstrate error handling
# 5. Implement a retry mechanism for failed steps
# 6. Show how to log and report errors
# 7. Demonstrate graceful degradation when a step fails

import uuid
import yaml
import time
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an agent for error handling demonstration
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Error Handler",
    about="An AI agent specialized in demonstrating error handling and recovery mechanisms.",
    model="gpt-4-turbo",
)

# Defining a task with potential errors and recovery mechanisms
task_def = yaml.safe_load("""
name: Error Handling Demo

input_schema:
  type: object
  properties:
    operation:
      type: string
      enum: ["divide", "api_call", "process_data"]
    value:
      type: number

tools:
- name: divide
  type: function
  function:
    name: divide
    description: Divide 100 by the given number
    parameters:
      type: object
      properties:
        divisor:
          type: number

- name: api_call
  type: integration
  integration:
    provider: httpbin
    method: get

- name: process_data
  type: function
  function:
    name: process_data
    description: Process the given data
    parameters:
      type: object
      properties:
        data:
          type: string

main:
- switch:
    value: inputs[0].operation
    cases:
      divide:
        - tool: divide
          arguments:
            divisor: inputs[0].value
          on_error:
            retry:
              max_attempts: 3
              delay: 2
            fallback:
              return: "Error: Division by zero or invalid input"
      api_call:
        - tool: api_call
          arguments:
            endpoint: "/status/{{inputs[0].value}}"
          on_error:
            retry:
              max_attempts: 3
              delay: 5
            fallback:
              return: "Error: API call failed after multiple attempts"
      process_data:
        - evaluate:
            data: "'Sample data: ' + str(inputs[0].value)"
        - tool: process_data
          arguments:
            data: _.data
          on_error:
            log: "Error occurred while processing data"
            return: "Error: Data processing failed"

- prompt:
    role: system
    content: >-
      Summarize the result of the operation:
      Operation: {{inputs[0].operation}}
      Result: {{_}}
""")

# Creating the task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Function to execute task and handle errors
def execute_task_with_error_handling(operation, value):
    try:
        execution = client.executions.create(
            task_id=TASK_UUID,
            input={"operation": operation, "value": value}
        )
        
        print(f"Executing {operation} with value {value}...")
        
        # Stream execution to show progress and potential retries
        for step in client.executions.transitions.stream(execution_id=execution.id):
            if step.type == "tool_call":
                print(f"Step: {step.tool}")
                if step.status == "error":
                    print(f"Error occurred: {step.error}")
                    if step.retry:
                        print(f"Retrying... (Attempt {step.retry.attempt})")
            elif step.type == "error":
                print(f"Task error: {step.error}")
        
        # Get final execution result
        result = client.executions.get(execution.id)
        print(f"Final result: {result.output}")
        
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# Demonstrate error handling for different scenarios
print("1. Division by zero (with retry and fallback):")
execute_task_with_error_handling("divide", 0)

print("\n2. API call with server error (with retry):")
execute_task_with_error_handling("api_call", 500)

print("\n3. Data processing error (with logging):")
execute_task_with_error_handling("process_data", "invalid_data")

print("\n4. Successful operation:")
execute_task_with_error_handling("divide", 4)