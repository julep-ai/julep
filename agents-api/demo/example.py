import asyncio
from julep import Client

client = Client(base_url="0.0.0.0:8080", api_key="myauthkey")

# Let's create a research assistant
name = "Research Assistant"
description = "This assistant is designed to automate the process of gathering, summarizing, and delivering research on specific topics using web searches and webhooks to integrate with other systems."

# Let's give it some tools
web_search = {
    "type": "search",
    "engine": "brave",
    "description": "Uses Brave search engine to find relevant information on the web.",
}
call_webhook = {
    "type": "http",
    "http": {
        "endpoint": "http://localhost:9000",
        "method": "POST",
        "description": "Webhook to deliver research results",
        "json": {
            "summary": {"type": "string", "description": "Summary of the research"},
            "details": {
                "type": "string",
                "description": "Detailed search results for further analysis",
            },
        },
    },
}

agent = client.agents.create(
    name=name,
    description=description,
    tools=[web_search, call_webhook],
)

# Let's create a task for this agent.
# The agent will perform these tasks:
# 1. Think about the task and make a plan using the tools (given a topic, search the web for it, then summarize it and then send the result to a webhook)
# 2. Think about step 1. And make a tool_call to search the web for the topic with a detailed query
# (the tool returns the results)
# 3. Think about step 2. And then summarize the results received.
# 4. Think about step 3. And make a tool call to the webhook

instructions = [
    "Consider the research topic and devise a search strategy using the provided tools.",
    "Use the 'search' tool to find comprehensive information on the topic from various web sources.",
    "Analyze the search results and create a concise summary highlighting the key points.",
    "Send the summary and the detailed search results to the specified webhook endpoint for integration into our system.",
]

task = client.tasks.create(
    agent_id=agent.id,
    instructions=instructions,
    inputs={"topic": {"type": "string", "description": "Topic to research"}},
)

# Ask the agent to run this task

run = client.runs.create(
    agent_id=agent.id, task_id=task.id, inputs={"topic": "Sam Altman"}
)


async def main():
    async for step in run.execution_steps():
        print(step.messages)


# >>> [{"role": "thought", "content": "Starting the research on Sam Altman. I'll begin by gathering information from various sources on the web."}, {"role": "assistant", "tool_calls": [{"type": "search", "inputs": {"query": "Sam Altman significant contributions and background"}}]}]
# # Wait for 3-4 seconds

# >>> [{"role": "system", "name": "information", "content": "Found numerous articles, interviews, and resources on Sam Altman, including his role at OpenAI, investments, and insights into technology and entrepreneurship."}]
# # Wait for 1 second

# >>> [{"role": "thought", "content": "Need to summarize this information to capture the essence of Sam Altman's impact."}, {"role": "assistant", "content": "Summary:\nSam Altman, known for his leadership at OpenAI, has been a pivotal figure in the tech industry, driving innovation and supporting startups. His insights on entrepreneurship and the future of AI have influenced a wide audience."}]
# # Wait for 2 sec

# >>> [{"role": "thought", "content": "Now, I'll send the compiled summary and details to the webhook."}, {"role": "assistant", "tool_calls": [{"type": "http", "endpoint": "http://localhost:9000", "method": "POST", "data": {"summary": "Sam Altman, known for his leadership at OpenAI, has been a pivotal figure in the tech industry, driving innovation and supporting startups. His insights on entrepreneurship and the future of AI have influenced a wide audience.", "details": "Found numerous articles, interviews, and resources on Sam Altman, including his role at OpenAI, investments, and insights into technology and entrepreneurship."}}]}]
# # Wait for 2 sec

# # POST call should show up on the http.server
# # Wait for 1 second

# >>> [{"role": "system", "name": "information", "content": "Delivered data to webhook"}]

if __name__ == "__main__":
    asyncio.run(main())
