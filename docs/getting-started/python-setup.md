---
description: Get up and running with Julep AI's Model APIs.
---

# Model Quickstart

## Account setup

This model is currently in [_Beta_.](#user-content-fn-1)[^1]\
To get access to the model, [join the waitlist](https://www.julep.ai/).&#x20;

Once you have access to an API key, make sure to save it somewhere safe and do not share it with anyone.

***

## Setup

### Installing the SDK

{% tabs %}
{% tab title="Python" %}
#### Setup a virtual entironment

To create a virtual environment, Python supplies a built in [venv module](https://docs.python.org/3/tutorial/venv.html) which provides the basic functionality needed for the virtual environment setup. Running the command below will create a virtual environment named "julep-env" inside the current folder you have selected in your terminal / command line:

```sh
python -m venv julep-env
```

Once you’ve created the virtual environment, you need to activate it. On Windows, run:

```powershell
julep-env\Scripts\activate
```

On Unix or MacOS, run:

```bash
source julep-env/bin/activate
```

#### **Install the Julep AI SDK**

```bash
pip install --upgrade julep
```
{% endtab %}

{% tab title="Node" %}
**Install the Julep AI SDK**

```bash
npm @julep/sdk
```

```bash
yarn add @julep/sdk
```

```bash
pnpm i @julep/sdk
```
{% endtab %}
{% endtabs %}

### **Configure the client**

To send a request to Julep AI API, configure the `api_key` in the Julep client.

{% tabs %}
{% tab title="Python" %}
{% code overflow="wrap" %}
```python
from julep import Client

api_key = "<api-key>"

client = Client(api_key=api_key)
```
{% endcode %}
{% endtab %}

{% tab title="Node" %}
```javascript
const julep = require("@julep/sdk")

const apiKey = "<api-key>";

const client = new julep.Client({ apiKey });
```
{% endtab %}
{% endtabs %}

***

## **Making an API request**

`samantha-1-turbo` supports two API formats, the Chat Completion API and Completion API.

### Chat Completion API

Construct your input messages for the conversation in the following format.



{% tabs %}
{% tab title="Python" %}
<pre class="language-python"><code class="lang-python"><strong>messages = [
</strong>    {
        "role": "system",
        "name": "situation",
        "content": "You are a Julia, an AI waiter. Your task is to help the guests decide their order.",
    },
    {
        "role": "system",
        "name": "information",
        "content": "You are talking to Diwank. He has ordered his soup. He is vegetarian.",
    },
    {
        "role": "system",
        "name": "thought",
        "content": "I should ask him more about his food preferences and choices.",
    },
]
</code></pre>
{% endtab %}

{% tab title="Node" %}
<pre class="language-javascript" data-overflow="wrap"><code class="lang-javascript"><strong>const messages = [
</strong>    {
        "role": "system",
        "name": "situation",
        "content": "You are a Julia, an AI waiter. Your task is to help the guests decide their order.",
    },
    {
        "role": "system",
        "name": "information",
        "content": "You are talking to Diwank. He has ordered his soup. He is vegetarian.",
    },
    {
        "role": "system",
        "name": "thought",
        "content": "I should ask him more about his food preferences and choices.",
    },
]
</code></pre>
{% endtab %}
{% endtabs %}

Then, make a request to the chat completion endpoint. Given a prompt, the model will return one or more predicted completions and can also return the probabilities of alternative tokens at each position.



{% tabs %}
{% tab title="Python" %}
```python
chat_completion = client.chat.completions.create(
    model="julep-ai/samantha-1-turbo",
    seed=21,
    messages=messages,
    max_tokens=500,
    temperature=0.1
)

print(chat_completion.choices[0].message.content)
```
{% endtab %}

{% tab title="Node" %}
```javascript
client.chat.completions.create({
    model: "julep-ai/samantha-1-turbo",
    seed: 21,
    messages: messages,
    max_tokens: 500,
    temperature: 0.1
}).then(response => {
    console.log(response.choices[0].message.content);
}).catch(error => {
    throw error
});
```
{% endtab %}
{% endtabs %}



### Completion API

Construct your prompt for the conversation in the following format.

When using the **Completion API**, we use the ChatML framework to Chatml helps structure and organize conversations between humans and AI models. You can read more about [ChatML here](https://github.com/openai/openai-python/blob/main/chatml.md).&#x20;

A section of a ChatML prompt starts with a specific token,`<|im_start|>`and ends with another token, `<|im_end|>`. Below is an example of a prompt using ChatML with sections specific to using the Samantha models.

Take note that for a conversation to take place between the user and assistant, the last message must have the `role` of `assistant`. The content should be empty and leave out the `<|im_end|>` tag at the end

```python
prompt = """
<|im_start|>situation
You are a Julia, an AI waiter. Your task is to help the guests decide their order.<|im_end|>
<|im_start|>information
You are talking to Diwank. He has ordered his soup. He is vegetarian.<|im_end|>
<|im_start|>thought
I should ask him more about his food preferences and choices.<|im_end|>
<im_start|>assistant (Julia)
"""
```

Then, make a request to the chat completion endpoint. Given a prompt, the model will return one or more predicted completions and can also return the probabilities of alternative tokens at each position.

{% tabs %}
{% tab title="Python" %}
```python
completion = client.completions.create(
    model="julep-ai/samantha-1-turbo",
    seed=21,
    prompt=prompt,
    max_tokens=500,
    temperature=0.1,
)

print(completion.choices[0].text)
```
{% endtab %}

{% tab title="Node" %}
```javascript
client.completions.create({
    model: "julep-ai/samantha-1-turbo",
    seed: 21,
    prompt: prompt,
    max_tokens: 500,
    temperature: 0.1
}).then(response => {
    console.log(completion.choices[0].text);
}).catch(error => {
    throw error
});
```
{% endtab %}
{% endtabs %}

### Creating a conversational bot

Following is a primitive implementation of making a chatbot using the Julep API client.

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
    }
]

name = input("Enter name: ")

while True:
    user_content = input("User: ")
    messages.append({"role": "user", "name": name, "content": user_content})
    chat_completion = client.chat.completions.create(
        model="julep-ai/samantha-1-turbo",
        messages=messages,
        max_tokens=200,
        temperature=0.2,
    )
    response = chat_completion.choices[0].message.content
    print("Jessica: ", response)
    messages.append({"role": "assistant", "name": "Jessica", "content": response})
```
{% endcode %}

***

## curl

### **Configure URL and API Key**

Add the `JULEP_API_KEY` environment variables in your shell environment.

```bash
export JULEP_API_KEY='your-api-key'
```

### **Making the API request**

```bash
curl --location 'https://api-alpha.julep.ai/v1/completions' \
--header 'Authorization: Bearer $JULEP_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
       "model": "julep-ai/samantha-1-turbo",
       "prompt": "\n<|im_start|>situation\nYou are a Julia, an AI waiter. Your task is to help the guests decide their order.<|im_end|>\n<|im_start|>information\nYou are talking to Diwank. He has ordered his soup. He is vegetarian.<|im_end|>\n<|im_start|>thought\nI should ask him more about his food preferences and choices.<|im_end|>\n<im_start|>assistant (Julia)",
       "max_tokens": 500,
       "temperature": 0.1,
       "seed": 21
     }' | jq '.choices[0].text'
```

***

[^1]: It's not in beta thought right?
