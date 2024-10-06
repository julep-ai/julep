# Monitoring Task Executions Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for task execution monitoring
# 3. Define a multi-step task that simulates a complex workflow
# 4. Implement functions for:
#    a. Starting task execution
#    b. Monitoring execution progress
#    c. Handling execution status updates
#    d. Logging execution metrics
# 5. Execute the task and demonstrate real-time monitoring
# 6. Display execution summary and metrics

import uuid
import yaml
from julep import Client
import time

# Global UUIDs for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an agent for task execution monitoring
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Task Execution Monitor",
    about="An AI agent designed to monitor and manage complex task executions.",
    model="gpt-4-turbo",
)

# Defining a multi-step task that simulates a complex workflow
task_def = yaml.safe_load("""
name: Complex Workflow Simulation

input_schema:
  type: object
  properties:
    project_name:
      type: string
    data_size:
      type: integer

tools:
- name: data_processor
  type: integration
  integration:
    provider: mock
    setup:
      processing_time: 5  # Simulated processing time in seconds

- name: report_generator
  type: integration
  integration:
    provider: mock
    setup:
      generation_time: 3  # Simulated generation time in seconds

main:
- prompt:
    role: system
    content: >-
      Initiating project '{{inputs[0].project_name}}' with data size {{inputs[0].data_size}} units.
      Prepare for data processing and report generation.
  unwrap: true

- tool: data_processor
  arguments:
    data_size: inputs[0].data_size

- evaluate:
    processed_data: "Processed " + str(inputs[0].data_size) + " units of data"

- tool: report_generator
  arguments:
    data: outputs[2].processed_data

- prompt:
    role: system
    content: >-
      Project '{{inputs[0].project_name}}' completed.
      Data processed: {{outputs[2].processed_data}}
      Report generated: {{outputs[3]}}
      
      Summarize the project results.
  unwrap: true

- return: _
""")

# Creating the task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

def start_task_execution(project_name, data_size):
    """Start the task execution and return the execution object."""
    execution = client.executions.create(
        task_id=TASK_UUID,
        input={
            "project_name": project_name,
            "data_size": data_size
        }
    )
    print(f"Task execution started for project '{project_name}'")
    return execution

def monitor_execution_progress(execution_id):
    """Monitor the execution progress in real-time."""
    print("Monitoring execution progress:")
    for transition in client.executions.transitions.stream(execution_id=execution_id):
        print(f"Step: {transition.type}, Status: {transition.status}")
        if transition.status == "completed":
            print(f"  Output: {transition.output}")
        elif transition.status == "failed":
            print(f"  Error: {transition.error}")
        time.sleep(1)  # Add a small delay to simulate real-time monitoring

def get_execution_status(execution_id):
    """Get the current status of the execution."""
    execution = client.executions.get(execution_id)
    return execution.status

def log_execution_metrics(execution_id):
    """Log and display execution metrics."""
    print("\nExecution Metrics:")
    transitions = client.executions.transitions.list(execution_id=execution_id).items
    total_duration = sum(t.duration_ms for t in transitions)
    for transition in transitions:
        print(f"Step: {transition.type}, Duration: {transition.duration_ms}ms")
    print(f"Total Execution Time: {total_duration}ms")

# Main execution flow
def run_task_monitoring_demo():
    project_name = "Data Analysis Project"
    data_size = 1000

    print(f"Starting task execution for '{project_name}' with {data_size} units of data")
    execution = start_task_execution(project_name, data_size)

    monitor_execution_progress(execution.id)

    final_status = get_execution_status(execution.id)
    print(f"\nFinal Execution Status: {final_status}")

    if final_status == "completed":
        result = client.executions.get(execution.id)
        print("\nExecution Result:")
        print(result.output)

    log_execution_metrics(execution.id)

# Run the task monitoring demo
run_task_monitoring_demo()