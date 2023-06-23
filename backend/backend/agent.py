import logging
from typing import AsyncGenerator
from vocode.streaming.agent.base_agent import RespondAgent
from vocode.streaming.models.agent import AgentConfig, AgentType
from .generate import generate, sentence_stream, AGENT_NAME


STOP_TOKENS = ["<|", "\n\n", "? ?", "person (", "???", "person(", "? person", ". person"]


class SamanthaConfig(AgentConfig, type=AgentType.LLM.value):
    prompt_preamble: str


class SamanthaAgent(RespondAgent[SamanthaConfig]):
    def __init__(
        self,
        agent_config: SamanthaConfig,
        logger: logging.Logger | None = None,
        sender=AGENT_NAME,
        recipient="Human",
    ):
        super().__init__(agent_config)
        self.sender = sender
        self.recipient = recipient
        self.memory = []
        if self.agent_config.prompt_preamble:
            self.memory = [
                {"role": "system", "content": self.agent_config.prompt_preamble}
            ]

        if agent_config.initial_message:
            self.memory.append(
                {
                    "role": "assistant", 
                    "name": AGENT_NAME,
                    "content": agent_config.initial_message.text,
                }
            )
    
    def get_memory_entry(self, human_input, response):
        result = [{"role": "user", "content": human_input}]
        if response:
            result.append(
                {
                    "role": "assistant", 
                    "name": AGENT_NAME, 
                    "content": response,
                }
            )
        
        return result

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

        text = generate(self.memory, stop=STOP_TOKENS, stream=False)
        
        return text, False

    async def generate_response(
        self, 
        human_input, 
        conversation_id: str, 
        is_interrupt: bool = False,
    ) -> AsyncGenerator[str, None]:
        self.logger.debug("Samantha LLM generating response to human input")
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            self.memory.extend(self.get_memory_entry(human_input, cut_off_response))
            yield cut_off_response
            return
        
        self.memory.append(self.get_memory_entry(human_input, None))
        for sent in sentence_stream(
            generate(self.memory, stop=STOP_TOKENS, stream=True)
        ):
            yield sent
