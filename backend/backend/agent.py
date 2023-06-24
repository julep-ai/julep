import logging
from typing import AsyncGenerator, Optional
from vocode.streaming.agent.base_agent import RespondAgent
from vocode.streaming.models.agent import AgentConfig, AgentType, CutOffResponse
from contextlib import suppress
from .generate import generate, AGENT_NAME, ChatMLMessage


STOP_TOKENS = ["<|", "\n\n", "< |", "<\n|"]


class SamanthaConfig(AgentConfig, type=AgentType.LLM.value):
    prompt_preamble: str
    cut_off_response: Optional[CutOffResponse] = None


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
        self.memory = {}
    
    def _make_memory_entry(self, human_input, response):
        result = [{"role": "user", "content": human_input.strip()}]
        if response:
            result.append(
                ChatMLMessage(
                    role="assistant", 
                    name=AGENT_NAME, 
                    content=response,
                )
            )
        
        return result

    async def respond(
        self, 
        human_input, 
        conversation_id: str, 
        is_interrupt: bool = False,
    ) -> tuple[str, bool]:
        mem = self._init_memory(self.memory.get(conversation_id, []))
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            mem.extend(self._make_memory_entry(human_input, cut_off_response))
            self.memory[conversation_id] = mem
            
            return cut_off_response, False
        
        self.logger.debug("LLM responding to human input")

        response = generate(mem, stop=STOP_TOKENS)
        text = response["choices"][0]["text"]
        mem.extend(self._make_memory_entry(human_input, text))
        self.memory[conversation_id] = mem
        
        return text, False

    def _init_memory(self, mem):
        if mem:
            return mem
        
        if self.agent_config.prompt_preamble:
            mem = [
                ChatMLMessage(name="situation", role="system", content=self.agent_config.prompt_preamble)
            ]

        if self.agent_config.initial_message:
            mem.append(
                ChatMLMessage(
                    role="assistant", 
                    name=AGENT_NAME,
                    content=self.agent_config.initial_message.text,
                )
            )
        
        return mem

    async def generate_response(
        self, 
        human_input, 
        conversation_id: str, 
        is_interrupt: bool = False,
    ) -> AsyncGenerator[str, None]:
        self.logger.debug("Samantha LLM generating response to human input")
        mem = self._init_memory(self.memory.get(conversation_id, []))

        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            mem.extend(self._make_memory_entry(human_input, cut_off_response))
            self.memory[conversation_id] = mem
            
            yield cut_off_response
            return

        response = generate(mem, stop=STOP_TOKENS)
        text = response["choices"][0]["text"]
        mem.extend(self._make_memory_entry(human_input, text))
        self.memory[conversation_id] = mem
        self.logger.info(f"memory state: {self.memory}")

        yield text
        return

    def cleanup_memory(self, conversation_id):
        with suppress(KeyError):
            del self.memory[conversation_id]
