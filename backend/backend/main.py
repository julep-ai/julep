import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer, ElevenLabsSynthesizerConfig
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber, DeepgramTranscriberConfig
from vocode.streaming.client_backend.conversation import ConversationRouter
from vocode.streaming.models.message import BaseMessage
from dotenv import load_dotenv
from .logger import logger
from .agent import SamanthaAgent, SamanthaConfig

load_dotenv()


SAMANTHA_VOICE_ID = os.environ["SAMANTHA_VOICE_ID"] #"eu7pAsMtrspvm0ZVbiCr"


app = FastAPI(docs_url=None)


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
    agent=SamanthaAgent(
        SamanthaConfig(
            initial_message=BaseMessage(text="Hello!"),
            prompt_preamble="Samantha is talking to a person.",
        )
    ),
    synthesizer_thunk=synthesizer_thunk,
    logger=logger,
)

app.include_router(conversation_router.get_router())
app.mount("/", StaticFiles(directory="public", html=True), name="public")
app.mount("/static", StaticFiles(directory="public/static"), name="static")
