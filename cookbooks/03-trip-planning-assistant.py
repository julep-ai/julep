import uuid
import yaml
from julep import Client
import os

openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
brave_api_key = os.getenv("BRAVE_API_KEY")

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Jarvis"
about = "The original AI conscious the Iron Man."
default_settings = {
    "temperature": 0.7,
    "top_p": 1,
    "min_p": 0.01,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "length_penalty": 1.0,
    "max_tokens": 150,
}

agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4o",
)

# Defining a Task
# Defining the task
task_def = yaml.safe_load(f"""
name: Tourist Plan With Weather And Attractions

input_schema:
  type: object
  properties:
    locations:
      type: array
      items:
        type: string
      description: The locations to search for.

tools:
- name: wikipedia
  type: integration
  integration:
    provider: wikipedia

- name: weather
  type: integration
  integration:
    provider: weather
    setup:
      openweathermap_api_key: {openweathermap_api_key}

- name: internet_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: {brave_api_key}

main:
- over: inputs[0].locations
  map:
    tool: weather
    arguments:
      location: _

- over: inputs[0].locations
  map:
    tool: internet_search
    arguments:
      query: "'tourist attractions in ' + _"

# Zip locations, weather, and attractions into a list of tuples [(location, weather, attractions)]
- evaluate:
    zipped: |-
      list(
        zip(
          inputs[0].locations,
          [output['result'] for output in outputs[0]],
          outputs[1]
        )
      )


- over: _['zipped']
  parallelism: 3
  # Inside the map step, each `_` represents the current element in the list
  # which is a tuple of (location, weather, attractions)
  map:
    prompt:
    - role: system
      content: >-
        You are {{{{agent.name}}}}. Your task is to create a detailed itinerary
        for visiting tourist attractions in some locations.
        The user will give you the following information for each location:

        - The location
        - The current weather condition
        - The top tourist attractions
    - role: user
      content: >-
        Location: "{{{{_[0]}}}}"
        Weather: "{{{{_[1]}}}}"
        Attractions: "{{{{_[2]}}}}"
    unwrap: true

- evaluate:
    final_plan: |-
      '\\n---------------\\n'.join(activity for activity in _)
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
         "locations": ["New York", "London", "Paris", "Tokyo", "Sydney"]
    }
)

print(f"Execution ID: {execution.id}")

# Wait for the execution to complete
import time
time.sleep(200)

# Getting the execution details
# Get execution details
execution = client.executions.get(execution.id)
# Print the output
print(execution.output)
print("-"*50)

if 'final_plan' in execution.output:
    print(execution.output['final_plan'])

# Lists all the task steps that have been executed up to this point in time
transitions = client.executions.transitions.list(execution_id=execution.id).items

# Transitions are retreived in reverse chronological order
for transition in reversed(transitions):
    print("Transition type: ", transition.type)
    print("Transition output: ", transition.output)
    print("-"*50)