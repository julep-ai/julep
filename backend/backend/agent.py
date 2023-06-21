import logging
from typing import AsyncGenerator
from vocode.streaming.agent.base_agent import RespondAgent
from vocode.streaming.models.agent import AgentConfig, AgentType
#from .generate import generate


# FIXME: uncomment the import above once the problem with huggingface token will be solved
def generate(*args, **kwargs):
	yield ""


class SamanthaConfig(AgentConfig, type=AgentType.LLM.value):
    pass


class SamanthaAgent(RespondAgent[SamanthaConfig]):
    def __init__(
        self,
        agent_config: SamanthaConfig,
        logger: logging.Logger | None = None,
        openai_api_key: str | None = None,
    ):
        super().__init__(agent_config)
        self.memory = []
    
    def get_memory_entry(self, human_input, response):
        return f"{self.recipient}: {human_input}\n{self.sender}: {response}"

    async def respond(
        self, 
        human_input, 
        conversartion_id: str, 
        is_interrupt: bool = False,
    ) -> tuple[str, bool]:
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            return cut_off_response, False
        self.logger.debug("LLM responding to human input")
        
        text = ""
        for token in generate(human_input, max_new_tokens=80):
            text += token

        return text, False

    async def generate_response(
        self, 
        human_input, 
        conversartion_id: str, 
        is_interrupt: bool = False,
    ) -> AsyncGenerator[str, None]:
        self.logger.debug("Samantha LLM generating response to human input")
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            self.memory.append(self.get_memory_entry(human_input, cut_off_response))
            yield cut_off_response
            return
        
        self.memory.append(self.get_memory_entry(human_input, ""))
        for token in generate(human_input, max_new_tokens=80):
            yield token