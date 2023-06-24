import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer, ElevenLabsSynthesizerConfig
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber, DeepgramTranscriberConfig
from vocode.streaming.client_backend.conversation import ConversationRouter
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.models.websocket import AudioConfigStartMessage
from vocode.streaming.output_device.websocket_output_device import WebsocketOutputDevice
from dotenv import load_dotenv
from .logger import logger
from .agent import SamanthaAgent, SamanthaConfig

load_dotenv()


SAMANTHA_VOICE_ID = os.environ["SAMANTHA_VOICE_ID"] #"eu7pAsMtrspvm0ZVbiCr"


app = FastAPI(docs_url=None)


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
        optimize_streaming_latency=3,
        stability=0.5,
        similarity_boost=0.75,
    )
)

transcriber_thunk = lambda input_audio_config: DeepgramTranscriber(
    DeepgramTranscriberConfig.from_input_audio_config(
        input_audio_config,
    ),
    api_key=os.environ["DEEPGRAM_API_KEY"],
)

conversation_router = ConversationRouter(
    agent=SamanthaAgent(
        SamanthaConfig(
            initial_message=BaseMessage(text="Hello!"),
            prompt_preamble="Samantha is talking to a person.",
            allowed_idle_time_seconds=60,
        )
    ),
    synthesizer_thunk=synthesizer_thunk,
    logger=logger,
)

app.include_router(conversation_router.get_router())
app.mount("/", StaticFiles(directory="public", html=True), name="public")
app.mount("/static", StaticFiles(directory="public/static"), name="static")
