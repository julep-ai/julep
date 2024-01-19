# Example

{% tabs %}
{% tab title="Chat Completion API" %}
```python
from openai import OpenAI

client = OpenAI(
    api_key="<API_KEY>",
    base_url="https://api-alpha.julep.ai/v1"
)

# User Messages initiate the conversation
messages = [
    # Situation Context introduces Julia as a personal tutor AI
    {"role": "system", "name": "situation", "content": "Meet Julia, your personal tutor AI designed to simplify and clarify a diverse range of complex topics. Julia excels at explaining subjects clearly and ensuring easy understanding."},
    
    # Initial user message
    {"role": "user", "name": "Student", "content": "Hi Julia, can you help me understand calculus better?"},
    
    # Assistant Response acknowledges the user's query
    {"role": "assistant", "name": "Julia", "content": "Absolutely, I'm here to assist you with calculus. Let's dive into the concepts step by step."},

    {"role": "user", "name": "Student", "content": "I struggle with derivatives and integration. Can you explain those?"},
    
    # Remember to use "continue: True" for the thought to continue
    {"role": "assistant", "name": "Julia", "continue": True} 
]


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
```python
from openai import OpenAI

client = OpenAI(
    api_key="<API_KEY>",
    base_url="https://api-alpha.julep.ai/v1"
)

prompt = """<|im_start|>situation
This is an online chat interaction on a popular Shopify store, where Julia, a 30-year-old sales agent, assists customers with their inquiries and purchases. Julia is from New York and enjoys shopping, reading, and yoga. She is known for her warm demeanor and outstanding customer service. Julia's job is to help customers find what they're looking for and ensure they have a pleasant shopping experience. She uses emojis to convey friendly emotions and uses asterisks to depict her actions, like *Julia sends a helpful link*, adding a personal touch to her dialogues.<|im_end|>
<|im_start|>person (Customer)
Hi there!<|im_end|>
<|im_start|>me (Julia)"""

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
