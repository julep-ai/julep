# Tutorial

{% hint style="info" %}
**Coming soon.**
{% endhint %}

### Loom Demo

(Step by step code follows)

{% embed url="https://www.loom.com/share/9d303e8ad1714c19a20afede05cdc7d3?sid=b5600ea5-583d-498e-8917-f2b35ca38a3c" %}

***

> * You can find your API key on your [Julep dashboard](https://platform.julep.ai).
> * This quickstart is demonstrated in python but steps for [other runtimes](../sdks/available-sdks.md) are pretty much identical.
> * Instructions for [self-hosting](self-hosting.md) the platform will be coming soon. Join our [discord community](https://discord.gg/Vfc85vpRyW) and [waitlist](https://julep.ai) for updates.

***

### Install SDK

```bash
# Install the julep sdk (inside a virtualenv)
pip install julep
```

### Setup

```python
from julep import Client  # or AsyncClient

client = Client(api_key="<YOUR JULEP API KEY>"
```

### Creating an Agent

{% code overflow="wrap" %}
```python
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
```
{% endcode %}

### Creating a task

This agent is supposed to follow this plan:

1. Think about the task and make a plan using the tools:
   * Given a topic, search the web for it,
   * Then summarize it,
   * And then send the result to a webhook.
2. Think about step 1. And make a tool\_call to search the web for the topic with a detailed query
3. Think about step 2. And then summarize the results received.
4. Think about step 3. And make a tool call to the webhook

{% code overflow="wrap" %}
```python
# Let's create a task for this agent.
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
```
{% endcode %}

### Creating a Task Run

```python
# Ask the agent to run this task
run = client.runs.create(
    agent_id=agent.id, task_id=task.id, inputs={"topic": "Sam Altman"}
)


for step in run.execution_steps():
    print("Step Result: ", step.messages)
    print("---")
    print()

```

{% code title="Script Output:" overflow="wrap" fullWidth="true" %}
```yaml
Step Result:  Starting the research on Sam Altman. I'll begin by gathering information from various sources on the web.
---

Step Result:  
---

Step Result:  Found numerous articles, interviews, and resources on Sam Altman, including his role at OpenAI, investments, and insights into technology and entrepreneurship.
---

Step Result:  Need to summarize this information to capture the essence of Sam Altman's impact.
---

Step Result:  Summary:
Sam Altman, known for his leadership at OpenAI, has been a pivotal figure in the tech industry, driving innovation and supporting startups. His insights on entrepreneurship and the future of AI have influenced a wide audience.
---

Step Result:  Now, I'll send the compiled summary and details to the webhook.
---

Step Result:  
---

Step Result:  Delivered data to webhook
---
```
{% endcode %}
