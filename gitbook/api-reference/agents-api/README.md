# Agents API (alpha)

{% hint style="danger" %}
The Agents API is still in early alpha and while the API is generally stable, it may change in backwards-incompatible ways as we continue to test it.
{% endhint %}

The main objects that the agents API allows you to create / access are:

* [Agents](../../python-sdk-docs/julep/managers/agent.md): Program using language models for complex task execution.
* [Users](../../python-sdk-docs/julep/managers/user.md): Users are entities within Julep to track memories by.
* [Sessions](../../python-sdk-docs/julep/managers/session.md): Real-time user-AI agent interactions similar to chat completions etc but with access to agent memories and documents.
* [Memories](agents-api-3.md): Memories store events, beliefs, facts for personalized interactions.
* [Docs](agents-api-4.md): Documents managed for agents or users for retrieval augmented generation or RAG.
* [Tasks](agents-api-5.md): Defined operations with multiple steps, objectives, longer duration.
* [Task Runs](agents-api-6.md): An instance of a Task that was started by an Agent with some input.
