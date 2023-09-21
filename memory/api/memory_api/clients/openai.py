import openai
from memory_api.env import generation_auth_token, generation_url


openai.api_key = generation_auth_token
openai.api_base = generation_url


completion = openai.ChatCompletion
