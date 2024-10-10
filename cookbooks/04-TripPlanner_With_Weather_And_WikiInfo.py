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
task_def = yaml.safe_load("""
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
      openweathermap_api_key: "YOUR_API_KEY"

main:
- over: inputs[0].locations
  map:
    tool: weather
    arguments:
      location: _

- over: inputs[0].locations
  map:
    tool: wikipedia
    arguments:
      query: "_ + ' tourist attractions'"

- evaluate:
    zipped: "list(zip(inputs[0].locations, [output['result'] for output in outputs[0]], [output['documents'][0]['page_content'] for output in outputs[1]]))"  # [(location, weather, attractions)]

- over: _['zipped']
  parallelism: 3
  map:
    prompt:
    - role: system
      content: >-
        You are a travel assistant. Your task is to create a detailed itinerary for visiting tourist attractions in "{{_[0]}}" based on the weather conditions and the top tourist attractions provided.
        
        Current weather condition at "{{_[0]}}":
        "{{_[1]}}"

        Top tourist attractions in "{{_[0]}}":
        "{{_[2]}}"

        Suggest outdoor or indoor activities based on the above information.
    unwrap: true
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
time.sleep(10)

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution Output:")
print(execution.output)

# List all steps of the executed task
print("Execution Steps:")
transitions = client.executions.transitions.list(execution_id=execution.id).items
print("Execution Steps:")
for transition in transitions:
    print(transition)

# Stream the steps of the defined task
print("Streaming execution transitions:")
print(client.executions.transitions.stream(execution_id=execution.id))