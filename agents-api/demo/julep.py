import asyncio
import uuid
import httpx


PORT = 9000


class Step:
    def __init__(self, d):
        self._d = d
    
    @property
    def messages(self):
        return self._d.get("content", "")


class Client:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.agents = AgentManager()
        self.tasks = TaskManager()
        self.runs = RunManager()

class AgentManager:
    def create(self, name, description, tools):
        return Agent(name, description, tools)

class Agent:
    def __init__(self, name, description, tools):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.tools = tools

class TaskManager:
    def create(self, agent_id, instructions, inputs):
        return Task(agent_id, instructions, inputs)

class Task:
    def __init__(self, agent_id, instructions, inputs):
        self.id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.instructions = instructions
        self.inputs = inputs

class RunManager:
    def create(self, agent_id, task_id, inputs):
        return Run(agent_id, task_id, inputs)

class Run:
    def __init__(self, agent_id, task_id, inputs):
        self.agent_id = agent_id
        self.task_id = task_id
        self.inputs = inputs

    async def execution_steps(self):
        steps = [
            {"role": "thought", "content": "Starting the research on Sam Altman. I'll begin by gathering information from various sources on the web."},
            {"role": "assistant", "tool_calls": [{"type": "search", "inputs": {"query": "Sam Altman significant contributions and background"}}]},
            {"role": "system", "name": "information", "content": "Found numerous articles, interviews, and resources on Sam Altman, including his role at OpenAI, investments, and insights into technology and entrepreneurship."},
            {"role": "thought", "content": "Need to summarize this information to capture the essence of Sam Altman's impact."},
            {"role": "assistant", "content": "Summary:\nSam Altman, known for his leadership at OpenAI, has been a pivotal figure in the tech industry, driving innovation and supporting startups. His insights on entrepreneurship and the future of AI have influenced a wide audience."},
            {"role": "thought", "content": "Now, I'll send the compiled summary and details to the webhook."},
            {"role": "assistant", "tool_calls": [{"type": "http", "endpoint": f"http://localhost:{PORT}", "method": "POST", "data": {"summary": "Sam Altman, known for his leadership at OpenAI, has been a pivotal figure in the tech industry, driving innovation and supporting startups. His insights on entrepreneurship and the future of AI have influenced a wide audience.", "details": "Found numerous articles, interviews, and resources on Sam Altman, including his role at OpenAI, investments, and insights into technology and entrepreneurship."}}]},
            
            # TODO: @dmitry
            # Add a HTTP POST call after this step to 0.0.0.0:8080 with the results
            
            {"role": "system", "name": "information", "content": "Delivered data to webhook"}
        ]

        for step in steps:
            if 'tool_calls' in step:
                # Simulate tool call delay
                await asyncio.sleep(3 if step['role'] == 'assistant' else 2)
                for c in step["tool_calls"]:
                    if c.get("endpoint"):
                        async with httpx.AsyncClient() as client:
                            await client.post(c["endpoint"], json=c["data"])
            else:
                # Simulate thought and system message delay
                await asyncio.sleep(1)
            yield Step(step)
