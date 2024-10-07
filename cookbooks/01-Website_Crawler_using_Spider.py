import os
import uuid
import yaml
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = os.getenv("JULEP_API_KEY")
if not api_key:
    raise ValueError("JULEP_API_KEY not found in environment variables")

client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Jarvis"
about = "The original AI conscious the Iron Man."

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4o",
)

# Defining a Task
task_def = yaml.safe_load("""
name: Agent Crawler

tools:
- name: spider_crawler
  type: integration
  integration:
    provider: spider
    setup:
      spider_api_key: "{{SPIDER_API_KEY}}"

main:
- tool: spider_crawler
  arguments:
    url: '"https://spider.cloud"'
""")

# Creating/Updating a task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Creating an Execution
execution = client.executions.create(
    task_id=TASK_UUID,
    input={}
)

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution output:", execution.output)

# Listing all the steps of a defined task
transitions = client.executions.transitions.list(execution_id=execution.id).items
print("Execution transitions:", transitions)

# Streaming the execution steps
print("Streaming execution transitions:")
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)