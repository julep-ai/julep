import asyncio
import vocode.streaming.streaming_conversation
import vocode.streaming.constants
import vocode.streaming.streaming_conversation


async def _check_for_idle(self):
    while True:
        await asyncio.sleep(15)


vocode.streaming.streaming_conversation.StreamingConversation.check_for_idle = _check_for_idle


vocode.streaming.streaming_conversation.ALLOWED_IDLE_TIME = 3600
vocode.streaming.constants.ALLOWED_IDLE_TIME = 3600
