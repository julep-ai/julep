import logging
from pytz import timezone
from typing import AsyncGenerator, Optional, TypedDict
from vocode.streaming.agent.base_agent import RespondAgent
from vocode.streaming.models.agent import AgentConfig, AgentType, CutOffResponse
from contextlib import suppress
from .generate import (
    generate,
    AGENT_NAME,
    ChatMLMessage,
    ChatML,
    to_prompt,
    generate_with_memory,
)
from functools import lru_cache
from transformers import AutoTokenizer
from typing import Optional

from .beliefs import to_belief_chatml_msg, get_matching_beliefs

IST = timezone("Asia/Kolkata")
STOP_TOKENS = ["<|", "< |", "<\n|"]

user_name = "Diwank"
bot_name = "Samantha"

tokenizer_id = "julep-ai/samantha-33b"
tokenizer = AutoTokenizer.from_pretrained(tokenizer_id, use_fast=False)


@lru_cache
def count_tokens(prompt: str):
    tokens = tokenizer.encode(prompt)
    return len(tokens)


def truncate(
    chatml: ChatML, max_tokens: int = 1700, retain_if=lambda x: False
) -> ChatML:
    chatml_with_idx = list(enumerate(chatml))
    chatml_to_keep = [c for c in chatml_with_idx if retain_if(c[1])]
    budget = (
        max_tokens
        - sum([count_tokens(to_prompt([c[1]], suffix="")) for c in chatml_to_keep])
        - count_tokens("<|section|>me (Samantha)\n")
    )

    assert budget > 0, "retain_if messages exhaust tokens"

    remaining = [c for c in chatml_with_idx if not retain_if(c[1])]
    for i, c in reversed(remaining):
        c_len = count_tokens(to_prompt([c], suffix=""))

        if budget < c_len:
            break

        budget -= c_len
        chatml_to_keep.append((i, c))

    sorted_kept = sorted(chatml_to_keep, key=lambda x: x[0])
    return [c for _, c in sorted_kept]


class SamanthaMetadata(TypedDict):
    situation: str
    email: str


class SamanthaConfig(AgentConfig, type=AgentType.LLM.value):
    prompt_preamble: str
    cut_off_response: Optional[CutOffResponse] = None
    metadata: Optional[SamanthaMetadata] = None


class SamanthaAgent(RespondAgent[SamanthaConfig]):
    def __init__(
        self,
        agent_config: SamanthaConfig,
        logger: logging.Logger | None = None,
        sender=AGENT_NAME,
        recipient="Human",
    ):
        super().__init__(agent_config, logger=logger)
        self.sender = sender
        self.recipient = recipient
        self.situation = agent_config.metadata["situation"]
        self.email = agent_config.metadata["email"]
        self.memory = {}

    def _make_memory_entry(self, human_input, response):
        result = []

        if human_input:
            result.append(
                {"role": "user", "name": "Diwank", "content": human_input.strip()}
            )

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

        return [
            ChatMLMessage(role="system", name="situation", content=self.situation),
            ChatMLMessage(
                role="assistant",
                name=AGENT_NAME,
                content=self.agent_config.initial_message.text,
            ),
        ]

    async def _generate_response(
        self,
        human_input,
        conversation_id: str,
        is_interrupt: bool = False,
    ):
        self.logger.debug("Samantha LLM generating response to human input")
        resp = await generate_with_memory(
            human_input,
            self.email,
            conversation_id,
            self.situation,
        )

        yield resp["assistant_output"]

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

        # Add belief information
        belief = to_belief_chatml_msg(
            get_matching_beliefs(
                mem + [dict(role="user", content=human_input)], 0.5
            )
        )

        mem.append(belief)

        mem.extend(self._make_memory_entry(human_input, None))
        mem = truncate(mem, retain_if=lambda msg: msg.get("name") == "situation")
        response = generate(mem, stop=STOP_TOKENS)
        text = response["choices"][0]["text"]
        mem.extend(self._make_memory_entry(None, text))
        self.memory[conversation_id] = mem
        self.logger.debug(f"+++ {self.memory}")

        yield text

    def cleanup_memory(self, conversation_id):
        with suppress(KeyError):
            del self.memory[conversation_id]
