import fire
import uvicorn
from fastapi import FastAPI
from memory_api.routers import characters, sessions, embedder, users
from memory_api.routers.characters.db import init as characters_db_init
from memory_api.routers.sessions.db import init as sessions_db_init
from memory_api.routers.users.db import init as users_db_init


app = FastAPI()
app.include_router(characters.router)
app.include_router(sessions.router)
app.include_router(embedder.router)
app.include_router(users.router)


def main(host="127.0.0.1", port="8000", backlog=4096, timeout_keep_alive=30, workers=None, log_level="info"):
    uvicorn.run(
        "web:app",
        host=host,
        port=port,
        log_level=log_level,
        timeout_keep_alive=timeout_keep_alive,
        backlog=backlog,
        workers=workers,
    )


if __name__ == "__main__":
    characters_db_init()
    sessions_db_init()
    users_db_init()

    fire.Fire(main)
