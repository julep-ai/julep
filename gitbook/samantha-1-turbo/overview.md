---
description: >-
  Samantha-1 is a series of our specially fine-tuned models for human-like
  conversations and agentic capabilities.
---

# Overview

## `samantha-1-turbo`

`samantha-1-turbo` a conversational LLM, is a fine-tuned version of Mistral-7B-v0.1.

During the fine-tuning process, [35 open-source datase](#user-content-fn-1)[^1]ts were adapted to enhance the model's capabilities. Each dataset underwent formatting and revision to not only support a conversational structure involving multiple turns and participants, but also incorporate the ability for native function calling. This enabled the conversational LLM to seamlessly integrate conversational dynamics with function execution within the same context.

### Key Features

* Fine-tuned for human-like conversations.
* Handles multi-turn multi-participant conversations.
* Fine-tuned for function calling.
* Special context section for embedded Chain of Thought.
* Special context section for memory management.
* More control over anthropomorphic personality.

### Training

Model:

* Layers: 32
* Hidden Size: 4096
* Attention Heads: 32
* Context Length: 32768 (with Sliding Window Attention)
* Vocab Size: 32032

Software:

* PyTorch
* DeepSpeed
* Flash-Attention
* Axolotl

### Context Section

This model has the following context sections.

* `user`: Represent the user and user input.
* `assistant`: Represents the persona given to the LLM.
* `situation`: An equivalent of the `system` section in OpenAI and other models. Meant to give the background and set the conversation tone.
* `thought`: A section for doing Chain of Thought. Let's the model "think" before generating a final response in the`assistant` section.
* `information`: A section to store factual information and introduce context in order to enrich conversation.

The model and speaker sections can optionally include a name like `me (Samantha)` or `person (Dmitry)`

[Read more about Context Sections](overview.md#context-section)

### Usage

You will need an API key to inference the model.

Samantha can be inferenced using either the Chat Completion API or Completion API. For more details check out [Quickstart](python-setup.md).

{% tabs %}
{% tab title="Chat Completion API" %}
```python
messages = [
    {
        "role": "system",
        "name": "situation",
        "content": "You are a Julia, an AI waiter. Your task is to help the guests decide their order."
    },
    {
        "role": "system",
        "name": "information",
        "content": "You are talking to Diwank. He has ordered his soup. He is vegetarian."
    },
    {
        "role": "system",
        "name": "thought",
        "content": "I should ask him more about his food preferences and choices."
    }
]

```
{% endtab %}

{% tab title="Completion API" %}
```python
messages = """
<|im_start|>situation
You are a Julia, an AI waiter. Your task is to help the guests decide their order.<|im_end|>
<|im_start|>information
You are talking to Diwank. He has ordered his soup. He is vegetarian.
<|im_start|>thought
I should ask him more about his food preferences and choices.<|im_end|>
"""
```
{% endtab %}
{% endtabs %}

### Evaluation

Evaluations show that training fine tuning Mistral-7B with our dataset and format does not lead to catastrophic forgetting.

Benchmarks show that `samantha-1-turbo` retains most, if not all the qualities of Mistral with better results in EQBench and TruthfulQA, due to it's better emotional understanding and ability to use the `thought` section for more conversational questions.

| Benchmarks     | Samantha-1-Turbo | Mistral 7B |
| -------------- | ---------------- | ---------- |
| **EQBench**    | 57.6%            | 52.1%      |
| **TruthfulQA** | 43.57%           | 42.15%     |
| Hellaswag      | 79.07%           | 81.3%      |
| MMLU           | 57.7%            | 59.5%      |
| Arc            | 79%              | 80%        |

***

## Use Cases

* **Personal Assistants**: Create AI personal assistants with a fun and consistent personality.
* **Customer Service**: Automate customer service with a system that can remember past interactions and respond accordingly.
* **Empathetic systems**: For use cases such as therapeutic support, personal coaching, and companionship.
* **Games and Interactive Media**: Create engaging characters and interactive dialogues for games and media.
* **Community Engagement:** Connect and empower users to engage with brand communities on channels such as WhatsApp

[^1]: such as?

