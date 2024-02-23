---
description: API for creating and modifying Agents
---

# Agents

## List agents

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents" method="get" expanded="false" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Create a new agent

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents" method="post" expanded="false" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Get a specific agent by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Update an agent

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}" method="put" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete an agent

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## List all tools

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/tools" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Create a new tool for agent

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/tools" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Update a tool by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/tools/{tool_id}" method="put" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete a tool by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/agents/{agent_id}/tools/{tool_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}
