# User Management and Personalization Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for handling user management and personalization
# 3. Define a task for user registration and profile creation
# 4. Define a task for personalized content recommendation
# 5. Create sample users with different preferences
# 6. Demonstrate user registration and profile creation
# 7. Show personalized content recommendations for different users
# 8. Implement a function to update user preferences
# 9. Display updated personalized recommendations after preference changes

import uuid
import yaml
from julep import Client

# Global UUIDs for agent and tasks
AGENT_UUID = uuid.uuid4()
REGISTRATION_TASK_UUID = uuid.uuid4()
RECOMMENDATION_TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an agent for user management and personalization
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Personalization Assistant",
    about="An AI agent specialized in user management and personalized content recommendations.",
    model="gpt-4-turbo",
)

# Defining a task for user registration and profile creation
registration_task_def = yaml.safe_load("""
name: User Registration and Profile Creation

input_schema:
  type: object
  properties:
    username:
      type: string
    interests:
      type: array
      items:
        type: string

main:
- prompt:
    role: system
    content: >-
      You are a user registration assistant. Create a user profile based on the following information:
      Username: {{inputs[0].username}}
      Interests: {{inputs[0].interests}}
      
      Generate a brief bio and suggest some initial content preferences based on the user's interests.
  unwrap: true

- evaluate:
    user_profile: >-
      {
        "username": inputs[0].username,
        "interests": inputs[0].interests,
        "bio": _.split('\n\n')[0],
        "content_preferences": _.split('\n\n')[1]
      }

- return: outputs[1].user_profile
""")

# Creating the registration task
registration_task = client.tasks.create_or_update(
    task_id=REGISTRATION_TASK_UUID,
    agent_id=AGENT_UUID,
    **registration_task_def
)

# Defining a task for personalized content recommendation
recommendation_task_def = yaml.safe_load("""
name: Personalized Content Recommendation

input_schema:
  type: object
  properties:
    user_profile:
      type: object

tools:
- name: content_database
  type: integration
  integration:
    provider: mock
    setup:
      data: [
        {"id": 1, "title": "Introduction to AI", "category": "Technology"},
        {"id": 2, "title": "Healthy Eating Habits", "category": "Health"},
        {"id": 3, "title": "Financial Planning 101", "category": "Finance"},
        {"id": 4, "title": "The Art of Photography", "category": "Art"},
        {"id": 5, "title": "Beginner's Guide to Yoga", "category": "Fitness"}
      ]

main:
- tool: content_database
  arguments: {}

- prompt:
    role: system
    content: >-
      You are a content recommendation system. Based on the user's profile and the available content,
      recommend 3 pieces of content that best match the user's interests and preferences.
      
      User Profile:
      {{inputs[0].user_profile}}
      
      Available Content:
      {{outputs[0]}}
      
      Provide your recommendations in the following format:
      1. [Content ID] - [Content Title] - Reason for recommendation
      2. [Content ID] - [Content Title] - Reason for recommendation
      3. [Content ID] - [Content Title] - Reason for recommendation
  unwrap: true

- return: _
""")

# Creating the recommendation task
recommendation_task = client.tasks.create_or_update(
    task_id=RECOMMENDATION_TASK_UUID,
    agent_id=AGENT_UUID,
    **recommendation_task_def
)

# Function to register a user and create their profile
def register_user(username, interests):
    execution = client.executions.create(
        task_id=REGISTRATION_TASK_UUID,
        input={
            "username": username,
            "interests": interests
        }
    )
    result = client.executions.get(execution.id)
    return result.output

# Function to get personalized content recommendations
def get_recommendations(user_profile):
    execution = client.executions.create(
        task_id=RECOMMENDATION_TASK_UUID,
        input={
            "user_profile": user_profile
        }
    )
    result = client.executions.get(execution.id)
    return result.output

# Function to update user preferences
def update_user_preferences(user_profile, new_interests):
    user_profile["interests"] = list(set(user_profile["interests"] + new_interests))
    return user_profile

# Demonstrate user registration and personalization
print("Demonstrating User Management and Personalization:")

# Register users
user1 = register_user("alice", ["technology", "finance"])
user2 = register_user("bob", ["health", "fitness"])

print("\nUser Profiles:")
print(f"Alice: {user1}")
print(f"Bob: {user2}")

# Get personalized recommendations
print("\nPersonalized Recommendations:")
print("Alice's Recommendations:")
print(get_recommendations(user1))
print("\nBob's Recommendations:")
print(get_recommendations(user2))

# Update user preferences
print("\nUpdating User Preferences:")
updated_alice = update_user_preferences(user1, ["art"])
print(f"Alice's Updated Profile: {updated_alice}")

# Get updated recommendations
print("\nUpdated Personalized Recommendations for Alice:")
print(get_recommendations(updated_alice))