import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import vocode.streaming.streaming_conversation
from vocode.streaming.synthesizer.eleven_labs_synthesizer import (
    ElevenLabsSynthesizer,
    ElevenLabsSynthesizerConfig,
)
from vocode.streaming.transcriber.deepgram_transcriber import (
    DeepgramTranscriber,
    DeepgramTranscriberConfig,
)
from vocode.streaming.client_backend.conversation import ConversationRouter
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.models.websocket import AudioConfigStartMessage
from vocode.streaming.models.transcriber import TimeEndpointingConfig
from vocode.streaming.output_device.websocket_output_device import WebsocketOutputDevice
from dotenv import load_dotenv
from .logger import logger
from .agent import SamanthaAgent, SamanthaConfig, IST
from .generate import generate, AGENT_NAME, ChatMLMessage

vocode.streaming.streaming_conversation.ALLOWED_IDLE_TIME = 3600

load_dotenv()

STOP_TOKENS = ["<|", "\n\n", "< |", "<\n|"]

user_name = "Diwank"
bot_name = "Samantha"

current_situation = f"""{user_name} is demoing {bot_name}'s capabilities to an audience of some amazing people. Both {user_name} and {bot_name} are live on this call. They have both been working very hard on doing this demo for a long time and are excited and a bit nervous about it."""

SAMANTHA_VOICE_ID = os.environ["SAMANTHA_VOICE_ID"]  # "eu7pAsMtrspvm0ZVbiCr"


app = FastAPI(docs_url=None)


def init_agent():
    user_name = "Diwank"
    bot_name = "Samantha"
    now = datetime.now(IST)
    situation = f"""{bot_name} is talking to {user_name}. They are old friends and {bot_name} works for {user_name} as their personal assistant.

It is {now.strftime("%H:%M")} on {now.strftime("%w")}, {now.strftime("%Y-%m-%d")}. {current_situation}"""

    first_message_thought = f"""{user_name} has just added me to the demo call. There are so many people present here who are all excited about this! I should say hi to {user_name} and every one else."""
    prompt = [
        ChatMLMessage(role="system", name="situation", content=situation),
        ChatMLMessage(role="system", name="thought", content=first_message_thought),
    ]
    resp = generate(prompt, stop=STOP_TOKENS)
    text = resp["choices"][0]["text"]

    return SamanthaAgent(
        SamanthaConfig(
            initial_message=BaseMessage(text=text),
            prompt_preamble="Samantha is talking to her old time friend and boss, Diwank. They have known each other for months now and she kinda has a crush on him.",
            allowed_idle_time_seconds=3600,
        ),
        logger=logger,
    )


class SamanthaStreamingConversation(StreamingConversation):
    def terminate(self):
        if self.agent and hasattr(self.agent, "cleanup_memory"):
            self.agent.cleanup_memory(self.id)
        return super().terminate()


class SamanthaConversationRouter(ConversationRouter):
    def get_conversation(
        self,
        output_device: WebsocketOutputDevice,
        start_message: AudioConfigStartMessage,
    ) -> SamanthaStreamingConversation:
        transcriber = self.transcriber_thunk(start_message.input_audio_config)
        synthesizer = self.synthesizer_thunk(start_message.output_audio_config)
        synthesizer.synthesizer_config.should_encode_as_wav = True
        return SamanthaStreamingConversation(
            output_device=output_device,
            transcriber=transcriber,
            agent=self.agent,
            synthesizer=synthesizer,
            conversation_id=start_message.conversation_id,
            logger=self.logger,
        )


synthesizer_thunk = lambda output_audio_config: ElevenLabsSynthesizer(
    ElevenLabsSynthesizerConfig.from_output_audio_config(
        output_audio_config,
        voice_id=SAMANTHA_VOICE_ID,
        api_key=os.environ["ELEVENLABS_API_KEY"],
        optimize_streaming_latency=1,  # Set by Diwank
        stability=0.375,  # Set by Diwank
        similarity_boost=1.0,  # Set by Diwank
    ),
    logger=logger,
)


ep_config = TimeEndpointingConfig(time_cutoff_seconds=0.1)


transcriber_thunk = lambda input_audio_config: DeepgramTranscriber(
    DeepgramTranscriberConfig.from_input_audio_config(
        input_audio_config,
        mute_during_speech=True,
        language="en-US",
        model="general",
        tier="nova",
        keywords=["Samantha", "Diwank", "Pascal"],
        min_interrupt_confidence=0.7,
        endpointing_config=ep_config,
        smart_format=True,
        interim_results=True,
    ),
    api_key=os.environ["DEEPGRAM_API_KEY"],
    logger=logger,
    should_stream_interim=True,
)

conversation_router = ConversationRouter(
    agent_thunk=init_agent,
    synthesizer_thunk=synthesizer_thunk,
    logger=logger,
)

app.include_router(conversation_router.get_router())
app.mount("/", StaticFiles(directory="public", html=True), name="public")
app.mount("/static", StaticFiles(directory="public/static"), name="static")
