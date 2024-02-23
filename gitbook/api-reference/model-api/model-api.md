# Chat Completions

Our models are available behind a REST API. You can use this API to generate completions for your own applications.

The API is compatible with the [OpenAI API](https://beta.openai.com/docs/api-reference/introduction) and can be used as a drop-in replacement with its clients.

## Chat Completions API

Given a list of messages comprising a conversation, the model will return a response.

{% swagger src="../../.gitbook/assets/model-openapi.yaml" path="/chat/completions" method="post" expanded="true" %}
[model-openapi.yaml](../../.gitbook/assets/model-openapi.yaml)
{% endswagger %}
