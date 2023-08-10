from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from .session_entry import respond


app = FastAPI()


@app.post("/v1/completions")
async def completions(
    email: str,
    vocode_conversation_id: str,
    tasks: BackgroundTasks,
    name: Optional[str] = "Anonymous",
    user_input: Optional[str] = None,
    situation: Optional[str] = None,
    echo: bool = False,
):
    #tasks.add_task()

    result = await respond(
        email,
        vocode_conversation_id,
        name,
        user_input,
        situation,
        echo,
    )

    return result

