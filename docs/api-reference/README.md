
# Agents API

[![Run In Postman](https://run.pstmn.io/button.svg)](https://god.gw.postman.com/run-collection/33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336?action=collection%2Ffork\&source=rip\_markdown\&collection-url=entityId%3D33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336%26entityType%3Dcollection%26workspaceId%3D183380b4-f2ac-44ef-b018-1f65dfc8256b)

{% hint style="danger" %}
The Agents API is still in early alpha and while the API is generally stable, it may change in backwards-incompatible ways as we continue to test it.
{% endhint %}

The main objects that the agents API allows you to create / access are:

* [Agents](../../sdks/python-sdk-docs/agent.md): Program using language models for complex task execution.
* [Users](../../sdks/python-sdk-docs/user.md): Users are entities within Julep to track memories by.
* [Sessions](../../sdks/python-sdk-docs/session.md): Real-time user-AI agent interactions similar to chat completions etc but with access to agent memories and documents.
* [Memories](agents-api-3.md): Memories store events, beliefs, facts for personalized interactions.
* [Docs](agents-api-4.md): Documents managed for agents or users for retrieval augmented generation or RAG.
* [Tasks](agents-api-5.md): Defined operations with multiple steps, objectives, longer duration.
* [Task Runs](agents-api-6.md): An instance of a Task that was started by an Agent with some input.
