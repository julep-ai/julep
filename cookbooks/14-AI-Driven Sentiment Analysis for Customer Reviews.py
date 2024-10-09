# AI-Driven Sentiment Analysis for Customer Reviews

# Implementation Plan:

# Import necessary libraries.
# Initialize the Julep client with API keys.
# Define Agent:

# Create an agent for sentiment analysis.
# Create Sentiment Analysis Task:

# Define input schema for customer reviews.
# Utilize the huggingface tool for sentiment analysis.
# Use slack for sending insights.
# Define Task Steps:

# Tool Call: Use huggingface to analyze review sentiment.
# Evaluate: Categorize feedback as positive, negative, or neutral.
# Conditional Logic: Check the sentiment value.
# Categorize Feedback (Set): Assign categories based on sentiment.
# Send Insights: Send the insights to Slack or a logging system.



import uuid
import yaml
from julep import Client

# Initialize Julep client
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Global UUIDs for agent and tasks
AGENT_UUID = uuid.uuid4()
SENTIMENT_TASK_UUID = uuid.uuid4()

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Sentiment Analysis Assistant",
    about="An AI agent specialized in analyzing customer reviews to determine sentiment and generate insights.",
    model="gpt-4-turbo",
)

# Define the sentiment analysis task
sentiment_task_def = yaml.safe_load("""
name: Sentiment Analysis for Customer Reviews

input_schema:
  type: object
  properties:
    review:
      type: string

tools:
- name: huggingface
  type: integration
  integration:
    provider: huggingface
    setup:
      model_name: "distilbert-base-uncased-finetuned-sst-2-english"

- name: slack
  type: integration
  integration:
    provider: slack

main:
- tool: huggingface
  arguments:
    inputs:
      review: inputs[0].review

- evaluate:
    sentiment: outputs[0].label

- condition:
    condition: _.get('sentiment') == 'POSITIVE'
    then:
      - set:
          category: "Positive Feedback"
    else:
      - set:
          category: "Negative or Neutral Feedback"

- log:
    message: "Review Sentiment: {{outputs[0].sentiment}}"

- send_insights:
    tool: slack
    arguments:
      channel: "sentiment-insights"
      message: >-
        Sentiment Analysis Results:
        Review: {{inputs[0].review}}
        Sentiment: {{outputs[0].sentiment}}
        Category: {{outputs[0].category}}
""")

# Create the task in Julep
sentiment_task = client.tasks.create_or_update(
    task_id=SENTIMENT_TASK_UUID,
    agent_id=AGENT_UUID,
    **sentiment_task_def
)

# Function to analyze sentiment of a review
def analyze_sentiment(review):
    execution = client.executions.create(
        task_id=SENTIMENT_TASK_UUID,
        input={
            "review": review
        }
    )
    result = client.executions.get(execution.id)
    return result.output

# Example usage
sample_review = "The product quality is excellent and exceeded my expectations!"
print(analyze_sentiment(sample_review))
