# Langchain

**Installation**

```
pip install git+https://github.com/julep-ai/langchain.git
```



**Example 1 (LLM Usage):**

```python
from langchain.llms.julepai import JulepAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


llm = JulepAI(julepai_api_key="<API_KEY>")
conversation = """Sam: Good morning, team! Let's keep this standup concise. We'll go in the usual order: what you did yesterday, what you plan to do today, and any blockers. Alex, kick us off.
Alex: Morning! Yesterday, I wrapped up the UI for the user dashboard. The new charts and widgets are now responsive. I also had a sync with the design team to ensure the final touchups are in line with the brand guidelines. Today, I'll start integrating the frontend with the new API endpoints Rhea was working on. The only blocker is waiting for some final API documentation, but I guess Rhea can update on that.
Rhea: Hey, all! Yep, about the API documentation - I completed the majority of the backend work for user data retrieval yesterday. The endpoints are mostly set up, but I need to do a bit more testing today. I'll finalize the API documentation by noon, so that should unblock Alex. After that, I’ll be working on optimizing the database queries for faster data fetching. No other blockers on my end.
Sam: Great, thanks Rhea. Do reach out if you need any testing assistance or if there are any hitches with the database. Now, my update: Yesterday, I coordinated with the client to get clarity on some feature requirements. Today, I'll be updating our project roadmap and timelines based on their feedback. Additionally, I'll be sitting with the QA team in the afternoon for preliminary testing. Blocker: I might need both of you to be available for a quick call in case the client wants to discuss the changes live.
Alex: Sounds good, Sam. Just let us know a little in advance for the call.
Rhea: Agreed. We can make time for that.
Sam: """
instruction = "Identify the main objectives mentioned in this conversation."

prompt = PromptTemplate.from_template("{instruction}\n{conversation}")
llm_chain = LLMChain(prompt=prompt, llm=llm)
res = llm_chain.run(instruction=instruction, conversation=conversation)

print(res)
```



**Example 2 (Chat Model):**

```python
import json
from langchain.chat_models.julepai.prompts import SituationMessagePromptTemplate
from langchain.chat_models.julepai import ChatJulepAI
from langchain.schema import HumanMessage, SystemMessage, FunctionMessage


chat = ChatJulepAI(
    julepai_api_key="<API_KEY>", 
    model_name="julep-ai/samantha-1-turbo",
)

situation = "You are a helpful assistant"
situation_prompt = SituationMessagePromptTemplate.from_template("{situation}")
functions = [
    {
        "name": "generate_anagram",
        "description": "Generate an anagram of a given word",
        "parameters": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "The word to generate an anagram of"
                }
            },
            "required": [
                "word"
            ]
        }
    }
]

res = chat([
    situation_prompt.format(situation=situation),
    SystemMessage(name="functions", content=json.dumps(functions)),
    HumanMessage(content="Hi, could you generate an anagram for the word 'bird'?"),
    FunctionMessage(content="", name="auto", continue_=True),
])

print(res.content)
```
