---
description: API for creating and modifying docs
---

# Docs

## Get all docs (for an agent or user)

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/additional_info" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/additional_info" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Create a new doc (for agent or user)

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/additional_info" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/additional_info" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete a doc by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/additional_info/{additional_info_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/users/{user_id}/additional_info/{additional_info_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}
