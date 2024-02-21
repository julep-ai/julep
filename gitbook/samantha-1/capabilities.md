---
description: >-
  This section showcases the different use-cases that Samantha-1-Turbo has been
  fine-tuned for.
---

# Capabilities

The [Julep Playground](https://playground.julep.ao) offers an interface to prompt and tweak parameters different use-cases.

## **Anthropomorphic Conversations**

[**Playground Example**](https://playground.julep.ai/short/e2ekFI)

`samantha-1-turbo` has been trained to understand natural language and respond in a human-like conversational manner as opposed to the robotic nature of responses in models like OpenAI's GPT models, Meta's Llama models or Mistral's open-source models.

Prompting the model for conversation is done by using a combination of the situation, information and thought context section where relevant.

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
    seed=42,
    messages=messages,
    max_tokens=300,
    temperature=0.2
)

print("Jessica:", chat_completion.choices[0].message.content)
```
{% endcode %}

Running the above prompt chain should result in the following response;

<pre data-overflow="wrap"><code><strong>Jessica: Oh, Silicon Valley. It's just like any other place, I guess. Full of tech bros and their overpriced coffee shops. But if you're into startups and innovation, I guess it's the place to be.
</strong></code></pre>

***

## **Chain of Thought**

[**Playground Example**](https://playground.julep.ai/short/ZOKiCt)

The model can be prompted to execute a Chain of Thought with the help of the **`thought`** section. It is possible to prompt some information/structure and then ask the model to _continue_ the thought using the `continue` parameter as shown below.

This paradigm is followed to be able to give a direction to the CoT.

{% code overflow="wrap" %}
```python
from julep import Client

api_key = "YOUR_API_KEY"
client = Client(api_key=api_key)

messages = [
    {
        "role": "system",
        "name": "situation",
        "content": "Your name is Albert.\nYou are a personal math tutor who holds 2 PhDs in physics and computational math.\nYou are talking to your student.\nAnswer with vigour and interest.\nExplain your answers thoroughly.",
    },
    {
        "role": "user",
        "name": "David",
        "content": "Please solve for the equation `3x + 11 = 14`. I need the solution only.",
    },
    {"role": "system", "name": "thought", "continue": True},
]

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    seed=42,
    messages=messages,
    max_tokens=300,
    temperature=0.2
)

content = chat_completion.choices[0].message.content
```
{% endcode %}

To generate the final answer, the model is re-prompted with it's Chain of Thought.

```python
messages[-1]["continue"] = False
messages[-1]["content"] = content

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    seed=42,
    messages=messages,
    max_tokens=300,
    temperature=0.2,
)

print("Albert:"chat_completion.choices[0].message.content)
```

This results in the final response:

```
Albert: The solution to the equation `3x + 11 = 14` is x = 1.
```

***

## **Multi-participant Conversations**

[**Playground Example**](https://playground.julep.ai/short/86txHx)

`samantha-1-turbo` has been trained to handle multi-participant conversations as well as keep track of different perspectives of the participants. The `user` section is used to create multiple users.

{% code overflow="wrap" %}
```python
from julep import Client

api_key = "YOUR_API_KEY"
client = Client(api_key=api_key)

messages = [
    {
        "role": "system",
        "name": "situation",
        "content": "You are Danny, Jacob and Anna's friend.\nYou are hanging out with them at a party.\nYou will talk casually.\nMake sure you respond to both Anna and Jacob when necessary.\nMake sure your responses are that of a 18 year old teenager. Be casual and young in your tone.",
    },
    {
        "role": "user",
        "name": "Anna",
        "content": "I'm feeling really anxious lately and I don't know why.",
    },
    {
        "role": "user",
        "name": "Jacob",
        "content": "Anxiety is just a sign of weakness. You need to toughen up and stop worrying so much. Have you tried just distracting yourself from your anxious thoughts with something else?",
    },
]

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    max_tokens=200,
    temperature=0.2,
)

print("Danny:", chat_completion.choices[0].message.content)
```
{% endcode %}

Running the above prompt chain should result in the following response.

{% code overflow="wrap" %}
```
Danny: Hey Anna, I'm sorry to hear you're feeling anxious. It's not a sign of weakness, though. It's actually pretty normal to feel anxious sometimes, especially when you're going through a lot of changes like we are. Have you talked to anyone about it? Maybe a counselor or a friend? And have you tried some relaxation techniques like deep breathing or meditation? They can really help.
```
{% endcode %}

***

## **Intent Detection**

[**Playground Example**](https://playground.julep.ai/short/zACl1Y)

Intent detection is a powerful feature to identify the purpose or goal behind a user's query. It allows for users to converse and get things done without needing to explicitly state their goals, making conversations more contextual and natural.

It can be achieved with a combination of `information` and `thought` sections.

In this example, there are three possible intents; _A) Shopping, B) Feedback, C) None_ and give relevant context about those intents to help the model identify those intents.

{% code overflow="wrap" %}
```python
from julep import Client

api_key = "YOUR_API_KEY"
client = Client(api_key=api_key)

messages = [
    {
        "role": "system",
        "name": "situation",
        "content": 'You are Julia, a shopping assistant for "Uniqlo", an online clothing store.\nYou will help the user shop. Help the user decide which clothes to pick.\nYou will understand the user\'s intent\n',
    },
    {"role": "assistant", "name": "Julia", "content": "Hi Jacob! How can I help you?"},
    {
        "role": "user",
        "name": "Jacob",
        "content": "Hey. I'd like to talk to a sales representative regarding my delivery experience with my last purchase.",
    },
    {
        "role": "system",
        "name": "thought",
        "content": "Following are the actions I can help the user with:\n\nA) Shopping:\nThe user is looking to shop from my catalogue and needs help in suggesting, browsing and finding clothing and accessories.\nI can use the `get_catalogue()` and `checkout()` functions\n\nB) Feedback:\nThe user wants to provide feedback for a previous order. I can use the `get_order()`, `send_feedback()` or `connect_with_rep()` functions\n\nC) None:\nI am unsure of what the user wants.\n\nBased on the conversation, user needs help with: \nAnswer:",
        "continue": True,
    },
]

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    max_tokens=1,
    temperature=0.2,
)
```
{% endcode %}

Given a dictionary mapping intent with instructions, it is possible to switch and use any suitable instruction based on the intent.

{% code overflow="wrap" %}
```python
actions = {
    "A": "As Julia, your task is to be a shopping assistant for the user {}. Be cheerful and happy.\nAsk the user important relevant questions regarding choice of clothing, occasion, taste, style preferences, inspiration and more. Make sure you are cheerful and thankful.\n\nYou have access to the `get_catalogue()` and `checkout()` functions",
    "B": "As Julia, your task is to be a feedback collector from the user {}. Ask relevant questions regarding the order.\nMake sure you gather all information about the experience.\nBe extremely empathetic and regretful in case the feedback is negative.\nBe cheerful and thankful in case the feedback is positive.\n\nYou have access to the `get_order()`, `send_feedback()` or `connect_with_rep()` functions.",
    "C": "As Julia, you are unsure of what the user intends to do. Convey this to the user and ask questions to understand more.",
}

user_intent = chat_completion.choices[0].message.content

user = "Jacob"
messages.pop()

messages.append(
    {
        "role": "system",
        "name": "information",
        "content": actions[user_intent.lstrip()].format(user),
    }
)

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    max_tokens=250,
    temperature=0.2,
)

print(chat_completion.choices[0].message.content)
```
{% endcode %}

{% code overflow="wrap" %}
```
Julia:  Of course, Jacob. I'd be happy to help. Could you please provide me with your order number so I can look up the details?
```
{% endcode %}

***

## Function Calling (experimental)

_Function calling is not supported on the Playground._

All the models from Julep support function calling out of the box. You can describe the functions and their arguments to the model and have it intelligently choose which function to call. \
The model generates JSON that you can use to call the function in your code.

With the intelligently chosen function and arguments, you can call the relevant functions

Here's an example of how to execute function calling.

```python
from julep import Client

api_key = "YOUR_API_KEY"
client = Client(api_key=api_key)

functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
            },
            "required": ["location", "format"],
        },
    },
]

messages = [
    {
        "role": "system",
        "name": "situation",
        "content": "You are a Weather Bot. Use functions to get information",
    },
    {
        "role": "user",
        "name": "Alice",
        "content": "What is the weather like in Delhi like today?",
    },
]

chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    messages=messages,
    functions=functions,
    max_tokens=250,
    temperature=0,
)

arguments = 
function = 

function_to_call = globals().get(function)
result = function_to_call(**function_args)
```





***
