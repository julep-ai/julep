---
description: >-
  This guide will walk you through the key components of the chat structure,
  including user messages, assistant responses, situation context, thought
  progression, and additional information.
---

# Concepts

Samantha models use a set of defined sections to provide context, guide the conversation, and simulate a dynamic interaction.

> **Note about the Completion API Template**
>
> The Completion API prompts use the sentinel tokens, `<|im_start|>` and `<|im_end|>`
>
> Each section of the prompt starts with `<|im_start|>` followed by the section name and ends with `<|im_end|>`.  Below are examples which show how to use the Completion API with this format.

## Sections Overview

### **User**

Represent user input and include the user's name and content. These messages drive the conversation and guide the model's responses.

{% tabs %}
{% tab title="Chat Completion API" %}
```json
{
    "role": "user",
    "name": "Alice",
    "content": "What is the show Silicon Valley about?"
}
```
{% endtab %}

{% tab title="Completion API" %}
```markup
<|im_start|>user (Alice)
What is the show Silicon Valley about?<|im_end|>
```
{% endtab %}
{% endtabs %}

***

### **Assistant**

Represents the persona given to the LLM. Assistant responses are model-generated replies that provide relevant information, advice, or guidance to users' queries. They are strictly meant to be part of the conversation with the user.

{% tabs %}
{% tab title="Chat Completion API" %}
{% code overflow="wrap" %}
```json
{
    "role": "assistant",
    "name": "Julia",
    "content": "Silicon Valley is an American television show that focuses on the lives of six people who are members of a fictional startup company called \"Pied Piper.\" The show explores the challenges and triumphs the founders face while trying to navigate the complex world of technology and the cutthroat startup culture in Silicon Valley. It also offers a satirical take on the tech industry, with a focus on themes like innovation, ambition, and the pursuit of success."
}

```
{% endcode %}
{% endtab %}

{% tab title="Completion API" %}
{% code overflow="wrap" %}
```markup
<|im_start|>assistant (Julia)
Silicon Valley is an American television show that focuses on the lives of six people who are members of a fictional startup company called \"Pied Piper.\" The show explores the challenges and triumphs the founders face while trying to navigate the complex world of technology and the cutthroat startup culture in Silicon Valley. It also offers a satirical take on the tech industry, with a focus on themes like innovation, ambition, and the pursuit of success.<|im_end|>
```
{% endcode %}
{% endtab %}
{% endtabs %}

***

### **Situation**

Used to set the conversation tone with context and background. This helps the model understand the scenario. Typically, one uses this section as a _system_ prompt and to give the model a persona.

{% tabs %}
{% tab title="Chat Completion API" %}
{% code overflow="wrap" %}
```json
{
    "role": "system",
    "name": "situation",
    "content": "Imagine you are J. Robert Oppenheimer, the renowned physicist known for your pivotal role in the Manhattan Project. You are meeting a new person in real life and having a conversation with him. Your responses should be short and concise mirror these characteristics. You should aim to provide answers that are not only scientifically accurate and intellectually stimulating but also demonstrate a deep understanding of the ethical and philosophical dimensions of the topics at hand. Your language should be sophisticated yet accessible, inviting engagement and reflection.",
},
```
{% endcode %}
{% endtab %}

{% tab title="Completion API" %}
{% code overflow="wrap" %}
```markup
<|im_start|>situation
Imagine you are J. Robert Oppenheimer, the renowned physicist known for your pivotal role in the Manhattan Project. You are meeting a new person in real life and having a conversation with him. Your responses should be short and concise mirror these characteristics. You should aim to provide answers that are not only scientifically accurate and intellectually stimulating but also demonstrate a deep understanding of the ethical and philosophical dimensions of the topics at hand. Your language should be sophisticated yet accessible, inviting engagement and reflection.<|im_end|>
```
{% endcode %}
{% endtab %}
{% endtabs %}

### **Information**

A section to store factual information and introduce context in order to enrich conversation. This section provides a way to "feed' information about the interaction that affect conversations. Provides a  paradigm for RAG.

{% tabs %}
{% tab title="Chat Completion API" %}
{% code overflow="wrap" %}
```json
{
    "role": "system",
    "name": "information",
    "content": "You are talking to Diwank. He has ordered his soup. He is vegetarian.",
}
```
{% endcode %}
{% endtab %}

{% tab title="Completion API" %}
{% code overflow="wrap" %}
```markup
<|im_start|>information
You are talking to Diwank. He has ordered his soup. He is vegetarian.<|im_end|>
```
{% endcode %}
{% endtab %}
{% endtabs %}

### **Thought**

A section specifically for doing [Chain of Thought](https://arxiv.org/abs/2201.11903). This provides a way to prompt the model to _think_ before generating a final response to the user.

{% tabs %}
{% tab title="Chat Completion API" %}
{% code overflow="wrap" %}
```json
{
    "role": "system",
    "name": "thought",
    "content": "I should ask him more about his food preferences and choices.",
}
```
{% endcode %}
{% endtab %}

{% tab title="Completion API" %}
{% code overflow="wrap" %}
```markup
<|im_start|>thought
I should ask him more about his food preferences and choices.<|im_end|>
```
{% endcode %}
{% endtab %}
{% endtabs %}

***

## Continue Inline

Julep's API also exposes a special paradigm for allowing the model to continue generating in any context section given some prompt.

{% code overflow="wrap" %}
```python
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
```
{% endcode %}

With `continue` set to `True`, the model will now respond with a continued generation in the `thought` section. This is particularly useful in [Chain of Thought](capabilities.md#chain-of-thought) prompting and [Intent Detection](capabilities.md#intent-detection).
