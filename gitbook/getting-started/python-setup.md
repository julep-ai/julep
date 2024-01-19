# Python Setup

To access our model via the OpenAI API, follow these steps:

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
