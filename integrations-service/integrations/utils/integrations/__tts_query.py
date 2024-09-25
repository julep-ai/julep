import os

from langchain_community.tools import ElevenLabsText2SpeechTool


async def tts_query(arguments: dict) -> str:
    """
    Converts text to speech using ElevenLabs API and plays the generated audio.
    """
    text_to_speak = arguments.get("query")
    if not text_to_speak:
        raise ValueError("Query parameter is required for text to speech")

    eleven_api_key = os.getenv("ELEVEN_API_KEY")

    tts = ElevenLabsText2SpeechTool(eleven_api_key=eleven_api_key)

    speech_file = tts.run(text_to_speak)

    return tts.play(speech_file)
