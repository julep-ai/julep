---
description: API for creating and modifying Sessions
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# Sessions

## List sessions

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Create a new session

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Get a specific session by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Update a specific session by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}" method="put" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Delete a specific session by id

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}" method="delete" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Chat

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}/chat" method="post" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Get suggestions made by the agent based on the session

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}/suggestions" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}

***

## Get a session's chat history

{% swagger src="../../.gitbook/assets/agents-openapi.yaml" path="/sessions/{session_id}/history" method="get" %}
[agents-openapi.yaml](../../.gitbook/assets/agents-openapi.yaml)
{% endswagger %}
