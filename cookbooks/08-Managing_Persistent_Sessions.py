# Managing Persistent Sessions Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for handling persistent sessions
# 3. Define a task for managing user context
# 4. Create a function to simulate user interactions
# 5. Implement a loop to demonstrate persistent sessions with context management
# 6. Show how to handle context overflow
# 7. Display the session history and context at the end

import uuid
import yaml
from julep import Client
import time

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an agent for handling persistent sessions
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Session Manager",
    about="An AI agent specialized in managing persistent sessions and context.",
    model="gpt-4o",
)

# Defining a task for managing user context
task_def = yaml.safe_load(f"""
name: Manage User Context

input_schema:
  type: object
  properties:
    user_input:
      type: string
    session_context:
      type: object

main:
- prompt:
  - role: system
    content: >-
      You are a session management agent. Your task is to maintain context
      across user interactions. Here's the current context: {{inputs[0].session_context}}
      
      User input: {{inputs[0].user_input}}
      
      Respond to the user and update the context with any new relevant information.
  unwrap: true
                          
- evaluate:
    session_context: >-
      {
        **inputs[0].session_context, 
       'last_interaction': inputs[0].user_input,
       'agent_response': _}                          

- return: 
    response: _
    context: outputs[1].session_context
""")

# Creating the task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Function to simulate user interactions
def user_interaction(prompt):
    return input(prompt)

# Create a session
session = client.sessions.create(
    agent=agent.id,
    context_overflow="adaptive"  # Use adaptive context management
)

# Initialize session context
context = {}

# Simulate a conversation with persistent context
for i in range(5):
    user_input = user_interaction(f"User (Interaction {i+1}): ")
    
    # Execute the task with user input and current context
    execution = client.executions.create(
        task_id=TASK_UUID,
        input={
            "user_input": user_input,
            "session_context": context
        }
    )
    
    # Get the execution result
    result = client.executions.get(execution.id)

    # Wait for the execution to complete
    time.sleep(2)
    
    # Update the context and print the response
    final_response = client.executions.transitions.list(execution_id=result.id).items[0].output
    print(final_response)
    # print(client.executions.transitions.list(execution_id=result.id).items[0])
    context = final_response['session_context']
    print(f"Agent: {final_response['session_context']['agent_response']}")
    print(f"Updated Context: {context}")
    print()
    
    # Simulate a delay between interactions
    time.sleep(1)

# Display final session information
print("Final Session Information:")
print(f"Session ID: {session.id}")
print(f"Final Context: {context}")

# Demonstrate context overflow handling
print("\nDemonstrating Context Overflow Handling:")
large_input = "This is a very large input " * 1000  # Create a large input to trigger overflow
overflow_execution = client.executions.create(
    task_id=TASK_UUID,
    input={
        "user_input": large_input,
        "session_context": context
    }
)

overflow_result = client.executions.get(overflow_execution.id)
# Wait for the execution to complete
time.sleep(2)
overflow_response = client.executions.transitions.list(execution_id=overflow_result.id).items[0].output
print(f"Agent response to large input: {overflow_response['session_context']['agent_response']}")
print(f"Updated context after overflow: {overflow_response['session_context']}")

# Display session history
print("\nSession History:")
history = client.sessions.history(session_id=session.id)
print(history)
