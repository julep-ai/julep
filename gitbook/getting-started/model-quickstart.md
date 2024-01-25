# Model Quickstart

You can access our model through one of these:
1. `openai` client of your choice, or
1. Our model playground available at [playground.julep.ai](https://playground.julep.ai), or
1. Direct HTTP requests to our endpoints.

*****

## Openai client example (python)

1. **Installation**

Make sure you have the `openai` Python package installed. If it's not already installed, you can add it to your environment by executing the following command:

```bash
pip install openai
```

2. **Credentials**

You can obtain your API\_KEY from our dashboard

```bash
api_key = "<API_KEY>"
base_url = "https://api-alpha.julep.ai/v1"
```

3. **Creating the Client**

To establish a connection with the API, you need to create a client instance using the `openai` package

```python
from openai import OpenAI

client = OpenAI(
    api_key=api_key
    base_url=base_url
)
```

4. **Examples**

{% tabs %}
{% tab title="Chat Completion API" %}
Construct your input messages for the conversation in the following format.

Take note that in order for a conversation to take place between the user and assistant, the last message must have the `role` of `assistant` with the property `continue` set to  `True` and removing the `content` property.

```python
messages = [
        {"role": "system", "name": "situation", "content": "Samantha is talking to Homer"},
        {"role": "user", "name": "Homer", "content": "Hi, how's it going?"},
        {"role": "assistant", "name": "Samantha", "content": "Hello, I am doing well, how are you?"},
        {"role": "user", "name": "Homer", "content": "I am good too"},
        {"role": "assistant", "name": "Samantha", "continue": True }
]

```

Then, make a request to the chat completion endpoint. Given a prompt, the model will return one or more predicted completions and can also return the probabilities of alternative tokens at each position.

```python
chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    max_tokens=120,
    stop=["<", "<|"],
    temperature=0.8,
    frequency_penalty=0.75
)

print(chat_completion.choices[0].message.content)
```
{% endtab %}

{% tab title="Completion API" %}
Construct your prompt for the conversation in the following format.

Take note that for a conversation to take place between the user and assistant, the last message must have the `role` of `assistant`. The content should be empty and leave out the `<|im_end|>` tag at the end

<pre><code><strong>prompt = '''
</strong>&#x3C;|im_start|>situation
Samantha is talking to Homer&#x3C;|im_end|>
&#x3C;|im_start|>user (Homer)
Hi, how's it going?&#x3C;|im_end|>
&#x3C;|im_start|>assistant (Samantha)
Hello, I am doing well, how are you?&#x3C;|im_end|>
&#x3C;|im_start|>user (Homer)
I am good too&#x3C;|im_end|>
&#x3C;|im_start|>assistant (Samantha)'''
</code></pre>

Then, make a request to the chat completion endpoint. Given a prompt, the model will return one or more predicted completions and can also return the probabilities of alternative tokens at each position.

```
completion = client.completions.create(
  model="julep-ai/samantha-1-turbo",
  prompt=prompt,
  max_tokens=120,
  temperature=0.8,
  frequency_penalty=0.75,
)

print(completion.choices[0].text)
```
{% endtab %}
{% endtabs %}

* **Fetch list of models**

```
openai.Model.list()
```

*****

## Model playground

Head over to [playground.julep.ai](https://playground.julep.ai), paste your API key and tinker with the model.

### Screenshot

<figure><img src=".gitbook/assets/playground-screenshot.png" alt=""><figcaption></figcaption></figure>

*****

## HTTP requests

Here's a generic example of how to make a POST request to the `samantha-1-turbo` API.

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
