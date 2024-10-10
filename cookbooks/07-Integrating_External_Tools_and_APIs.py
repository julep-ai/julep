import uuid
import yaml
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Multi-Tool Analyst"
about = "An AI agent capable of using multiple external tools and APIs to gather and analyze information."

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4-turbo",
)

# Defining a Task
task_def = yaml.safe_load("""
name: Comprehensive Analysis Report

input_schema:
  type: object
  properties:
    topic:
      type: string
      description: The main topic to analyze.
    location:
      type: string
      description: A location related to the topic for weather and news analysis.

tools:
- name: brave_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "YOUR_BRAVE_API_KEY"

- name: weather
  type: integration
  integration:
    provider: weather
    setup:
      openweathermap_api_key: "YOUR_OPENWEATHERMAP_API_KEY"

- name: wikipedia
  type: integration
  integration:
    provider: wikipedia

main:
- tool: brave_search
  arguments:
    query: "{{inputs[0].topic}} latest developments"

- tool: weather
  arguments:
    location: "{{inputs[0].location}}"

- tool: wikipedia
  arguments:
    query: "{{inputs[0].topic}}"

- prompt:
  - role: system
    content: >-
      You are a comprehensive analyst. Your task is to create a detailed report on the topic "{{inputs[0].topic}}" 
      using the information gathered from various sources. Include the following sections in your report:
      
      1. Overview (based on Wikipedia data)
      2. Latest Developments (based on Brave Search results)
      3. Weather Impact (if applicable, based on weather data for {{inputs[0].location}})
      4. Analysis and Conclusions
      
      Use the following data for your report:
      
      Brave Search Results: {{outputs[0]}}
      Weather Data: {{outputs[1]}}
      Wikipedia Data: {{outputs[2]}}
      
      Provide a well-structured, informative report that synthesizes information from all these sources.
  unwrap: true

- return: _
""")

# Creating/Updating a task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Creating an Execution
execution = client.executions.create(
    task_id=task.id,
    input={
        "topic": "Renewable Energy",
        "location": "Berlin, Germany"
    }
)

print(f"Execution ID: {execution.id}")

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution Output:")
print(execution.output)

# List all steps of the executed task
print("Execution Steps:")
for item in client.executions.transitions.list(execution_id=execution.id).items:
    print(item)

# Stream the execution steps in real-time
print("Streaming Execution Steps:")
for step in client.executions.transitions.stream(execution_id=execution.id):
    print(step)