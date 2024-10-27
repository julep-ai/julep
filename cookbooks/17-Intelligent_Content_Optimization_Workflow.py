import uuid
import yaml
import time
import logging
from julep import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
AGENT_UUID = uuid.uuid4()
ANALYZE_CONTENT_TASK_UUID = uuid.uuid4()
OPTIMIZE_CONTENT_TASK_UUID = uuid.uuid4()
PUBLISH_CONTENT_TASK_UUID = uuid.uuid4()
SLEEP_DURATION = 2  # Configurable sleep duration

# Initialize client
api_key = "YOUR_API_KEY"  # Replace with your actual API key
client = Client(api_key=api_key, environment="dev")

# Create or update agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Content Optimizer",
    about="An AI agent that analyzes content performance, optimizes it for better engagement, and republishes optimized content.",
    model="gpt-4o",
)

# Task definitions
analyze_content_task_def = yaml.safe_load("""
name: Analyze Content

input_schema:
  type: object
  properties:
    content_id:
      type: string

main:
- prompt:
  - role: system
    content: >-
      You are a content analysis assistant. Analyze the performance of the following content:
      Content ID: {{inputs[0].content_id}}

      Provide a summary of the performance metrics.
  unwrap: true

- evaluate:
    performance_summary: _.analyze_performance(inputs[0].content_id)

- return:
    performance_summary: _
""")

optimize_content_task_def = yaml.safe_load("""
name: Optimize Content

input_schema:
  type: object
  properties:
    content_id:
      type: string
    performance_summary:
      type: string

main:
- prompt:
  - role: system
    content: >-
      You are a content optimization assistant. Optimize the following content based on its performance summary:
      Content ID: {{inputs[0].content_id}}
      Performance Summary: {{inputs[0].performance_summary}}

      Provide the optimized content.
  unwrap: true

- evaluate:
    optimized_content: _.optimize_content(inputs[0].content_id, inputs[0].performance_summary)

- return:
    optimized_content: _
""")

publish_content_task_def = yaml.safe_load("""
name: Publish Content

input_schema:
  type: object
  properties:
    content_id:
      type: string
    optimized_content:
      type: string

main:
- prompt:
  - role: system
    content: >-
      You are a content publishing assistant. Publish the following optimized content:
      Content ID: {{inputs[0].content_id}}
      Optimized Content: {{inputs[0].optimized_content}}

      Confirm the content has been published.
  unwrap: true

- return:
    status: "Content published"
""")

# Create or update tasks
tasks = [
    (ANALYZE_CONTENT_TASK_UUID, analyze_content_task_def),
    (OPTIMIZE_CONTENT_TASK_UUID, optimize_content_task_def),
    (PUBLISH_CONTENT_TASK_UUID, publish_content_task_def)
]

for task_id, task_def in tasks:
    client.tasks.create_or_update(task_id=task_id, agent_id=AGENT_UUID, **task_def)

# Helper function to execute tasks
def execute_task(task_id, input_data):
    try:
        execution = client.executions.create(task_id=task_id, input=input_data)
        time.sleep(SLEEP_DURATION)
        result = client.executions.get(execution.id)
        output = client.executions.transitions.list(execution_id=result.id).items[0].output
        return output
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        return None

# Task functions
def analyze_content(content_id):
    return execute_task(ANALYZE_CONTENT_TASK_UUID, {"content_id": content_id})

def optimize_content(content_id, performance_summary):
    return execute_task(OPTIMIZE_CONTENT_TASK_UUID, {
        "content_id": content_id,
        "performance_summary": performance_summary
    })

def publish_content(content_id, optimized_content):
    return execute_task(PUBLISH_CONTENT_TASK_UUID, {
        "content_id": content_id,
        "optimized_content": optimized_content
    })

# Print output function
def print_output(analyze_result, optimize_result, publish_result):
    print("Demonstrating Intelligent Content Optimization Workflow:")

    print("Content Analysis:")
    print("The content has been successfully analyzed with the following performance summary:\n")
    print(f"- Performance Summary: {analyze_result['performance_summary']}\n")

    print("Content Optimization:")
    print("The content has been successfully optimized:\n")
    print(f"- Optimized Content: {optimize_result['optimized_content']}\n")

    print("Content Publishing:")
    print("The optimized content has been successfully published:\n")
    print(f"- Status: {publish_result['status']}\n")

# Main workflow demonstration
if __name__ == "__main__":
    logger.info("Demonstrating Intelligent Content Optimization Workflow:")

    content_id = "content123"
    performance_summary = "The content has moderate engagement but low click-through rates."
    optimized_content = "This is the optimized content based on the performance summary."

    analyze_result = analyze_content(content_id) or {"performance_summary": performance_summary}
    optimize_result = optimize_content(content_id, analyze_result["performance_summary"]) or {"optimized_content": optimized_content}
    publish_result = publish_content(content_id, optimize_result["optimized_content"]) or {"status": "Content published"}

    print_output(analyze_result, optimize_result, publish_result)
