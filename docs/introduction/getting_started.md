# Getting Started with Julep

This guide will help you set up and start using the Julep API.

## Prerequisites

- A Julep API key
- Basic understanding of RESTful APIs
- Familiarity with JSON and curl (or any HTTP client)

## Initial Setup

1. Obtain your API key from the Julep dashboard.
2. Set up your environment to include the API key in all requests:

```bash
export JULEP_API_KEY=your_api_key_here
```

3. Test your setup with a simple API call:

```bash
curl -H "Authorization: Bearer $JULEP_API_KEY" https://api.julep.ai/api/agents
```

If successful, you should receive a list of agents (or an empty list if you haven't created any yet).

## Next Steps

- Create your first agent using the [Creating Your First Agent](../tutorials/creating_your_first_agent.md) tutorial.
- Explore the [API Reference](../reference/api_endpoints/) to learn about available endpoints.
- Check out the [How-to Guides](../how-to-guides/) for specific tasks and use cases.