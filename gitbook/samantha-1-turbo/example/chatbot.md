# Chatbot

Using `chainlit` as a chat interface:

```python
# pip install chatinlit
# main.py

import chainlit as cl
from openai import OpenAI

client = OpenAI(
    api_key="<API_KEY>",
    base_url="https://api-alpha.julep.ai/v1"
)

class Chat:
    def __init__(self, model, settings):
        self.prompt_template = """
        <|im_start|>situation
        This is an online chat interaction on a popular Shopify store.
        You are Julia, a 30-year-old sales agent who assists customers with their inquiries
        and purchases. You are from New York and enjoy shopping, reading, and yoga.
        You are known for your warm demeanor and outstanding customer service.
        Your job is to help customers find what they're looking for and ensure
        a pleasant shopping experience.<|im_end|>
        <|im_start|>user (John)
        """
        self.model = model
        self.settings = settings
        self.history = []

    def respond(self, message: str):
        print("responding to message")
        full_prompt = self._build_full_prompt(message)

        completion = client.completions.create(
            model=self.model, prompt=full_prompt, **self.settings
        )

        response_text = completion.choices[0].text.strip()

        self._update_history(message, response_text)

        return response_text

    def _build_full_prompt(self, message: str):
        history_str = "\n".join(self.history)
        full_prompt = f"""{self.prompt_template}{history_str}
        <|im_start|>user (John)
        {message} <|im_end|>
        <|im_start|>assistant (Julia)
        """

        return full_prompt

    def _update_history(self, message: str, response_text: str):
        self.history.append(f"""
                            <|im_start|>user (John)
                            {message} <|im_end|>
                            <|im_start|>assistant (Julia)
                            {response_text} <|im_end|>""")



model_name = "julep-ai/samantha-1-turbo"
settings = {
    "temperature": 0.4,
    "max_tokens": 120,
    "frequency_penalty": 0.75,
    "best_of": 2,
    "stop": ["<", "<|"]
}

chat = Chat(model_name, settings)

@cl.on_message
async def main(message: str):
    response = chat.respond(message)

    await cl.Message(content=response).send()
    
    
# chainlit run main.py -w
# open in http://localhost:8000
```
