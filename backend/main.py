import os
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer, ElevenLabsSynthesizerConfig
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber, DeepgramTranscriberConfig
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.client_backend.conversation import ConversationRouter
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.agent import AgentConfig, AgentType
from vocode.streaming.agent.base_agent import RespondAgent
from dotenv import load_dotenv
from .generate import generate

load_dotenv()


SAMANTHA_VOICE_ID = os.environ["SAMANTHA_VOICE_ID"] #"eu7pAsMtrspvm0ZVbiCr"


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


app = FastAPI(docs_url=None)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

synthesizer_thunk = lambda output_audio_config: ElevenLabsSynthesizer(
    ElevenLabsSynthesizerConfig.from_output_audio_config(
        output_audio_config,
        voice_id=SAMANTHA_VOICE_ID,
        api_key=os.environ["ELEVENLABS_API_KEY"],
    )
)

transcriber_thunk = lambda input_audio_config: DeepgramTranscriber(
    DeepgramTranscriberConfig.from_input_audio_config(
        input_audio_config,
    ),
    api_key=os.environ["DEEPGRAM_API_KEY"],
)

conversation_router = ConversationRouter(
    agent=ChatGPTAgent(
        ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Hello!"),
            prompt_preamble="Have a pleasant conversation about life",
        )
    ),
    synthesizer_thunk=synthesizer_thunk,
    logger=logger,
)

app.include_router(conversation_router.get_router())
app.mount("/", StaticFiles(directory="static"), name="static")
