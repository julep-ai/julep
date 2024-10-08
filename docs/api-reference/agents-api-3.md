---
description: API for accessing Agent Memories
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# Memories

## Get an agent's memories

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/memories" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete a memory by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/memories/{memory_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}
