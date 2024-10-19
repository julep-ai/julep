# BASIC AGENT CREATION AND INTERACTION

import uuid
from julep import Client

# Global UUID is generated for agent
AGENT_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Jarvis"
about = "A friendly and knowledgeable AI assistant."
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

print(f"Agent created with ID: {agent.id}")

# Create a session for interaction
session = client.sessions.create(
    agent=agent.id
)

print(f"Session created with ID: {session.id}")

# Function to chat with the agent
def chat_with_agent(message):
    message = {
        "role": "user",
        "content": message,
    }
    response = client.sessions.chat(
        session_id=session.id,
        messages=[message],
    )
    return response.choices[0].message.content

# Demonstrate basic interaction
print("Agent: Hello! I'm Jarvis, your AI assistant. How can I help you today?")

while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Agent: Goodbye! It was nice chatting with you.")
        break
    
    response = chat_with_agent(user_input)
    print(f"Agent: {response}")

# Optional: Retrieve chat history
history = client.sessions.get(session_id=session.id)
print("\nChat History:")
print(history)