# Try it out

You can access our model through our dedicated endpoint or via the OpenAI API.

Here's a generic example of how to make a POST request to the `samantha-1-turbo` API.&#x20;

{% tabs %}
{% tab title="Request" %}
```bash
curl --location 'https://api-alpha.julep.ai/v1/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "prompt": "<|im_start|>Can you explain the concept of quantum entanglement?<|im_end|>",
    "temperature": 0.6,
    "max_tokens": 140,
    "best_of": 2
}'
```
{% endtab %}

{% tab title="Response" %}
```json
{
    "id": "cmpl-f4c1905e994444ffa34cf8788eca2e23",
    "object": "text_completion",
    "created": 1699303657,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "text": "<|im_start|> Quantum entanglement is a fundamental concept in quantum mechanics that refers to the phenomenon where two or more particles become interconnected in such a way that the state of one particle is dependent on the state of the other, regardless of the distance between them. This means that if the state of one particle is measured, the state of the other particle is determined as well, even if it is light-years away. This concept challenges our understanding of local realism and has significant implications for quantum computing and communication.",
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 14,
        "total_tokens": 119,
        "completion_tokens": 105
    }
}
```
{% endtab %}
{% endtabs %}
