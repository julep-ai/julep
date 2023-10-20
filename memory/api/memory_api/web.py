import fire
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from memory_api.routers import (
    characters, 
    sessions, 
    embedder, 
    users, 
    entries,
    models,
    personality,
    beliefs,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

app.include_router(characters.router)
app.include_router(sessions.router)
app.include_router(embedder.router)
app.include_router(users.router)
app.include_router(entries.router)
app.include_router(models.router)
app.include_router(personality.router)
app.include_router(beliefs.router)


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
    characters.db.init()
    sessions.db.init()
    users.db.init()
    entries.db.init()
    models.db.init()
    personality.db.init()
    beliefs.db.init()

    fire.Fire(main)
