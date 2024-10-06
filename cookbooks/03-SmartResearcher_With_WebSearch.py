import uuid
from julep import Client
import yaml

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

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4o",
)

# Defining a Task
task_def = yaml.safe_load("""
name: Research Assistant to find Wikipedia Keywords

input_schema:
  type: object
  properties:
    topics:
      type: array
      items:
        type: string
      description: The topics to search for.

tools:
- name: brave_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "YOUR_API_KEY"

main:
- over: _.topics
  map:
    tool: brave_search
    arguments:
      query: "'the latest news about ' + _"

- over: _
  parallelism: 2
  map:
    prompt:
    - role: system
      content: >-
        You are a research assistant.
        I need you to do in-depth research on topics trending in the news currently.
        Based on the following latest html news snippet, come up with a list of wikipedia keywords to search:
        "{{_}}"
        Your response should be a list of keywords, separated by commas. Do not add any other text.
        Example: `KEYWORDS: keyword1, keyword2, keyword3`

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
        "topics": ["Burger King Cup on the Ground Behind a Wendy's", "Forbidden Chemical X", "Finger Bracelets", "Amusing Notions"]
    }
)

print(execution.id)

# Getting the execution details
execution = client.executions.get(execution.id)
print(execution.output)

# Listing all the steps of a defined task
transitions = client.executions.transitions.list(execution_id=execution.id).items
print(transitions)

# Streaming the execution steps
client.executions.transitions.stream(execution_id=execution.id)