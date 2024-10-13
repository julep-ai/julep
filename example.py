import yaml
from julep import Julep

# Initialize the Julep client
client = Julep(api_key="your_julep_api_key")

# Step 1: Create an Agent
agent = client.agents.create(
    name="Storytelling Agent",
    model="gpt-4",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)

# Add an image generation tool (DALL·E) to the agent
client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_openai_api_key",
        },
    },
)

# Step 2: Create a Task that generates a story and comic strip
task_yaml = """
name: Story and Comic Creator
description: Create a story based on an idea and generate a 4-panel comic strip illustrating the story.

main:
  # Step 1: Generate a story and outline into 4 panels
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip.
          Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story.
    unwrap: true

  # Step 2: Extract the panel descriptions and story
  - evaluate:
      story: _.split('1. ')[0].strip()
      panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)

  # Step 3: Generate images for each panel using the image generator tool
  - foreach:
      in: _.panels
      do:
        tool: image_generator
        arguments:
          description: _

  # Step 4: Generate a catchy title for the story
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the story below, generate a catchy title.

          Story: {{outputs[1].story}}
    unwrap: true

  # Step 5: Return the story, the generated images, and the title
  - return:
      title: outputs[3]
      story: outputs[1].story
      comic_panels: "[output.image.url for output in outputs[2]]"
"""

task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)

# Step 3: Execute the Task
execution = client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# Watch as the story and comic panels are generated
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)

# Once the execution is finished, retrieve the results
result = client.executions.get(execution_id=execution.id)
print("Task Result:", result)

# Step 4: Chat with the Agent
session = client.sessions.create(agent_id=agent.id)

# Send messages to the agent
while True:
    message = input("Enter a message (or 'quit' to exit): ")
    if message.lower() == 'quit':
        break
    
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )
    print("Agent:", response.choices[0].message.content)

print("Chat session ended.")
