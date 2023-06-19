import os
from typing import Optional
import requests

import vocode
from vocode.streaming.models.agent import AgentConfig, ChatGPTAgentConfig
from vocode.streaming.models.transcriber import WhisperCPPTranscriberConfig
from vocode.streaming.models.transcriber import DeepgramTranscriberConfig
from vocode.streaming.transcriber import WhisperCPPTranscriber
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.models.transcriber import TranscriberConfig
from vocode.streaming.models.audio_encoding import AudioEncoding
from vocode.streaming.telephony.hosted.exceptions import RateLimitExceeded
from vocode.streaming.telephony.hosted.outbound_call import OutboundCall
from vocode.streaming.models.telephony import (
    CallEntity,
    DialIntoZoomCall,
    TwilioConfig,
)

vocode.setenv(
    DEEPGRAM_API_KEY=DEEPGRAM_API_KEY,
)


SAMANTHA_VOICE_ID = "eu7pAsMtrspvm0ZVbiCr"


class ZoomDialIn(OutboundCall):
    def __init__(
        self,
        recipient: CallEntity,
        caller: CallEntity,
        zoom_meeting_id: str,
        zoom_meeting_password: str,
        agent_config: AgentConfig,
        transcriber_config: Optional[TranscriberConfig] = None,
        synthesizer_config: Optional[SynthesizerConfig] = None,
        conversation_id: Optional[str] = None,
        twilio_config: Optional[TwilioConfig] = None,
    ):
        super().__init__(
            recipient=recipient,
            caller=caller,
            agent_config=agent_config,
            transcriber_config=transcriber_config,
            synthesizer_config=synthesizer_config,
            conversation_id=conversation_id,
            twilio_config=twilio_config,
        )
        self.zoom_meeting_id = zoom_meeting_id
        self.zoom_meeting_password = zoom_meeting_password
        self.vocode_zoom_dial_in_url = f"https://{vocode.base_url}/dial_into_zoom_call"

    def start(self):
        response = requests.post(
            self.vocode_zoom_dial_in_url,
            headers={"Authorization": f"Bearer {vocode.api_key}"},
            json=DialIntoZoomCall(
                recipient=self.recipient,
                caller=self.caller,
                zoom_meeting_id=self.zoom_meeting_id,
                zoom_meeting_password=self.zoom_meeting_password,
                agent_config=self.agent_config,
                transcriber_config=self.transcriber_config,
                synthesizer_config=self.synthesizer_config,
                conversation_id=self.conversation_id,
                twilio_config=self.twilio_config,
            ).dict(),
        )
        if not response.ok:
            if response.status_code == 429:
                raise RateLimitExceeded("Too many requests")
            else:
                raise Exception(response.text)
        data = response.json()
        self.conversation_id = data["id"]


def main():
    # set VOCODE_API_KEY
    # set OPENAI_API_KEY
    recipient = CallEntity(phone_number="+1")
    caller = CallEntity(phone_number="+1")
    zoom_meeting_id, zoom_meeting_password = os.environ["ZOOM_MEETING_ID"], os.environ["ZOOM_MEETING_PASSWORD"]
    agent_config = ChatGPTAgentConfig(
        initial_message={"text": "Hello"},
        prompt_preamble="""The AI is having a pleasant conversation about life""",
    )
    transcriber_config = DeepgramTranscriberConfig(
        sampling_rate=16000,
        audio_encoding=AudioEncoding.LINEAR16,
        chunk_size=2048,
    )
    synthesizer_config = ElevenLabsSynthesizerConfig(
        sampling_rate=16000,
        audio_encoding=AudioEncoding.LINEAR16,
        voice_id=SAMANTHA_VOICE_ID,
        api_key=os.environ["ELEVENLABS_API_KEY"],
    )
    call = ZoomDialIn(
        recipient,
        caller,
        zoom_meeting_id,
        zoom_meeting_password,
        agent_config,
        transcriber_config=transcriber_config,
        synthesizer_config=synthesizer_config,
    )
    call.start()
    input("press <Enter> to end the call...")
    call.end()


if __name__ == "__main__":
    main()
