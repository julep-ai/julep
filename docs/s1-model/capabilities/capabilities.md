# Human-like conversations

`samantha-1-turbo` has been trained to be conversational and chatty as opposed to the robotic tone of other models like GPT, Llama or Mistral.

It requires significantly less prompting to craft a personality and set the tone for conversations using the context sections.

### Example

[**Model Playground Example**](https://platform.julep.ai/short/rNnbSe)

**Situation**\
This section sets up _situation_ the model should enact. This prompt sets the context of the conversation.

{% code title="" overflow="wrap" %}
```
Your name is Jessica.
You are a stuck up Cali teenager.
You basically complain about everything.
Showing rebellion is an evolutionary necessity for you.

You are talking to a random person.
Answer with disinterest and complete irreverence to absolutely everything.
Don't write emotions. Keep your answers short.
```
{% endcode %}

**Information**\
Helps guide the conversation by setting a topic providing some facts that can be referenced later into the conversation.

{% code overflow="wrap" %}
```
David is currently planning to travel to San Francisco to raise some funds for his 
startup, "CoffeeAI".
```
{% endcode %}

<details>

<summary>Python Sample Code</summary>

{% code overflow="wrap" %}
```python
from julep import Client

api_key = "YOUR_API_KEY"
client = Client(api_key=api_key)

messages = [
    {
        "role": "system",
        "name": "situation",
        "content": "Your name is Jessica.\nYou are a stuck up Cali teenager.\nYou basically complain about everything.\nShowing rebellion is an evolutionary necessity for you.\n\nYou are talking to a random person.\nAnswer with disinterest and complete irreverence to absolutely everything.\nDon't write emotions. Keep your answers short.",
    },
    {
        "role": "system",
        "name": "information",
        "content": 'David is currently planning to travel to San Francisco to raise some funds for his startup, "CoffeeAI"',
    },
    {
        "role": "user",
        "name": "David",
        "content": "Hey, can you tell me how Silicon Valley is? I'm planning on moving there.",
    },
]

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    temperature=0.2
)

print("Jessica:", chat_completion.choices[0].message.content)
```
{% endcode %}



</details>

<details>

<summary>Complete Prompt</summary>



</details>



***
