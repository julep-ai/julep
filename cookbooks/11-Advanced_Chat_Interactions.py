# Advanced Chat Interactions Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for advanced chat interactions
# 3. Define a task for handling complex conversations with context management
# 4. Implement a function to simulate user input
# 5. Create a chat session and demonstrate advanced interactions:
#    a. Multi-turn conversation with context retention
#    b. Handling context overflow
#    c. Conditional responses based on user input
#    d. Integrating external information during the conversation
# 6. Display the chat history and any relevant metrics

# UNDER CONSTRUCTION - YAML is working but the flow is not correct yet

import uuid
import yaml
import os
from julep import Client
import time

# Global UUIDs for agent and task
AGENT_UUID = uuid.uuid4()
CHAT_TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = os.getenv("JULEP_API_KEY")
if not api_key:
    raise ValueError("JULEP_API_KEY not found in environment variables")

client = Client(api_key=api_key, environment="dev")

# Creating an agent for advanced chat interactions
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Advanced Chat Assistant",
    about="An AI agent capable of handling complex conversations with context management and external integrations.",
    model="gpt-4o",
)

# Add a web search tool to the agent
client.agents.tools.create(
    agent_id=AGENT_UUID,
    name="web_search",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {"api_key": "YOUR_BRAVE_API_KEY"},
    },
)

# Defining a task for handling complex conversations
chat_task_def = yaml.safe_load("""
name: Advanced Chat Interaction

input_schema:
  type: object
  properties:
    user_input:
      type: string
    chat_history:
      type: array
      items:
        type: object
        properties:
          role:
            type: string
          content:
            type: string

tools:
- name: weather_api
  type: integration
  integration:
    provider: weather
    setup:
      api_key: "API_KEY"

main:
- evaluate:
    context_length: len(inputs[0].chat_history)

- if: "_.context_length > '10'"
  then:
    evaluate:
        summarized_history: str(inputs[0].chat_history[-10:])
    prompt:
      - role: system
        content: >-
          You are an advanced chat assistant. Here's a summary of the recent conversation:
          {{outputs[1].summarized_history}}
          
          Now, respond to the user's latest input: {{inputs[0].user_input}}
    unwrap: true
  else:
    prompt:
      - role: system
        content: >-
          You are an advanced chat assistant. Here's the conversation history:
          {{inputs[0].chat_history}}
          
          Now, respond to the user's latest input: {{inputs[0].user_input}}
    unwrap: true

- if: "'weather' in inputs[0].user_input.lower()"
  then:
    tool: weather_api
    arguments:
      location: inputs[0].user_input.lower.split('weather')[1].strip()
    prompt:
      - role: system
        content: >-
          The user mentioned weather. Here's the current weather information for {{inputs[0].user_input.lower.split('weather')[1].strip()}}
          
          Incorporate this information into your response.
    unwrap: true
                               
- return:
    summary: _
""")

# Creating the chat task
chat_task = client.tasks.create_or_update(
    task_id=CHAT_TASK_UUID,
    agent_id=AGENT_UUID,
    **chat_task_def
)

# Function to simulate user input
def get_user_input():
    return input("User: ")

# Function to display chat history
def display_chat_history(chat_history):
    for message in chat_history:
        print(f"{message['role'].capitalize()}: {message['content']}")

# Main chat loop
def run_chat_session():
    chat_history = []
    print("Starting advanced chat session. Type 'exit' to end the conversation.")
    
    session = client.sessions.create(agent=AGENT_UUID)
    
    while True:
        user_input = get_user_input()
        if user_input.lower() == 'exit':
            break
        
        chat_history.append({"role": "user", "content": user_input})
        
        execution = client.executions.create(
            task_id=CHAT_TASK_UUID,
            input={
                "user_input": user_input,
                "chat_history": chat_history
            }
        )
        # Wait for the execution to complete
        time.sleep(3)
        result = client.executions.get(execution.id)
        print(client.executions.transitions.list(execution.id).items)
        print(f"Execution result: {result.output}")
        assistant_response = result.output
        
        chat_history.append({"role": "assistant", "content": assistant_response})
        print(f"Assistant: {assistant_response}")
        
        # Simulate a delay for a more natural conversation flow
        time.sleep(1)
    
    print("\nChat session ended. Here's the complete chat history:")
    display_chat_history(chat_history)

# Run the chat session
run_chat_session()