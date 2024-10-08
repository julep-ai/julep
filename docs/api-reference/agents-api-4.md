---
description: API for creating and modifying docs
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# Docs

## Get all docs (for an agent or user)

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/docs" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/docs" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Create a new doc (for agent or user)

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/docs" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/docs" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete a doc by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/docs/{doc_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/docs/{doc_id}" method="delete" %}

[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}
