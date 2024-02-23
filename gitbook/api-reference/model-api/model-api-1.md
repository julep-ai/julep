# Completions (Advanced)

Our models are available behind a REST API. You can use this API to generate completions for your own applications.

The API is compatible with the [OpenAI API](https://beta.openai.com/docs/api-reference/introduction) and can be used as a drop-in replacement with its clients.

## Completions API

Creates a completion for the provided prompt and parameters.

{% swagger src="../../.gitbook/assets/model-openapi.yaml" path="/completions" method="post" expanded="true" %}
[model-openapi.yaml](../../.gitbook/assets/model-openapi.yaml)
{% endswagger %}
