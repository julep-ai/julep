---
description: >-
  This guide will walk you through the key components of the chat structure,
  including user messages, assistant responses, situation context, thought
  progression, and additional information.
---

# Context "sections"

Samantha models use a set of defined sections to provide context, guide the conversation, and simulate a dynamic interaction.&#x20;

Samantha is compatible with the OpenAI API and can be called using either the Chat Completion API and Completion API.

{% tabs %}
{% tab title="Completion API" %}
When using the **Completion API**, we use the ChatML framework to Chatml helps structure and organize conversations between humans and AI models. You can read more about [ChatML here](https://github.com/openai/openai-python/blob/main/chatml.md). A section of a ChatML prompt starts with a specific token,`im_start`and ends with another token, `im_end`. Below is an example of a prompt using ChatML with sections specific to using the Samantha models.

```
'''
<|im_start|>situation
Julia is a personal tutor AI designed to teach and simplify a 
diverse range of complex topics. Julia excels at explaining subjects 
clearly and concisely.<|im_end|>
<|im_start|>user (Alice)
Hi there! Can you help me with my algebra homework?<|im_end|>
<|im_start|>assistant (Julia)
Of course, Alice! I'd be happy to assist you with your algebra homework. 
Please provide me with the details of the problem.<|im_end|>
<|im_start|>thought
Julia considers different approaches to explain algebra concepts 
clearly to Alice.<|im_end|>
<|im_start|>information
Alice's preferred learning style is visual, 
and she responds well to step-by-step explanations with examples.<|im_end|>
'''
```
{% endtab %}

{% tab title="Chat Completion API" %}


When using the **Chat Completion API**, dicts are used instead to enclose sections. The dicts equivalent of the ChatML prompt is as follows:

```
[
    {"role": "system", "name": "situation", "content": "Julia is a personal tutor AI designed to simplify and clarify a diverse range of complex topics. Julia excels at explaining subjects clearly and ensuring easy understanding."},
    {"role": "user", "name": "Alice", "content": "Hi there! Can you help me with my math homework?"},
    {"role": "assistant", "name": "Julia", "content": "Of course, Alice! I'd be happy to assist you with your math homework. Please provide me with the details of the problem."},
    {"role": "system", "name": "thought", "content": "Julia considers different approaches to explain algebra concepts clearly to Alice."},
    {"role": "system", "name": "information", "content": "Alice's preferred learning style is visual, and she responds well to step-by-step explanations with examples."}
]
```
{% endtab %}
{% endtabs %}

## Sections Overview

1. **User**:

* Represent user input and include the user's name and content. These messages drive the conversation and guide the model's responses

{% tabs %}
{% tab title="Completion API" %}
```python
'''<|im_start|>user (Alice)
Hi there! Can you help me with my math homework?<|im_end|>'''
```
{% endtab %}

{% tab title="Chat Completion API" %}
```python
{"role": "user", "name": "Alice", "content": "Hi there! Can you help me with my math homework?"}
```
{% endtab %}
{% endtabs %}

2. **Assistant**:

* Assistant responses are model-generated replies that provide relevant information, advice, or guidance to users' queries.&#x20;

{% tabs %}
{% tab title="Completion API" %}
```python
'''<|im_start|>assistant (Julia)
Of course, Alice! I'd be happy to assist you with your math homework. Please provide me with the details of the problem.<|im_end|>'''
```
{% endtab %}

{% tab title="Chat Completion API" %}
```
{"role": "assistant", "name": "Julia", "content": "Of course, Alice! I'd be happy to assist you with your math homework. Please provide me with the details of the problem."}
```
{% endtab %}
{% endtabs %}

3. **Situation**:

* Set the conversation tone with context and background information. This helps the model understand the scenario.

{% tabs %}
{% tab title="Completion API" %}
```
'''<|im_start|>situation
Julia is a personal tutor AI designed to simplify and clarify a diverse range of complex topics. Julia excels at explaining subjects clearly and ensuring easy understanding.<|im_end|>'''
```
{% endtab %}

{% tab title="Chat Completion API" %}
```
{"role": "system", "name": "situation", "content": "Julia is a personal tutor AI designed to simplify and clarify a diverse range of complex topics. Julia excels at explaining subjects clearly and ensuring easy understanding."}
```
{% endtab %}
{% endtabs %}

4. **Thought**:

* Thought sections enable the model to generate its own insights and queries, contributing to dynamic conversations. They simulate a chain of thought, allowing the model to expand on its responses.

{% tabs %}
{% tab title="Completion API" %}
```
'''<|im_start|>thought
Julia considers different approaches to explain algebra concepts clearly to Alice.<|im_end|>'''
```
{% endtab %}

{% tab title="Chat Completion API" %}
```
{"role": "system", "name": "thought", "content": "Julia considers different approaches to explain algebra concepts clearly to Alice."}
```
{% endtab %}
{% endtabs %}

5. **Information**:

* Additional information sections introduce context that enhances the conversation. This context might not be part of the immediate dialogue but enriches the interaction.

{% tabs %}
{% tab title="Completion API" %}
```
'''<|im_start|>information Alice's preferred learning style is visual, and she responds well to step-by-step explanations with examples.<|im_end|>'''
```
{% endtab %}

{% tab title="Chat Completion API" %}
```
{"role": "system", "name": "information", "content": "Alice's preferred learning style is visual, and she responds well to step-by-step explanations with examples."}
```
{% endtab %}
{% endtabs %}
