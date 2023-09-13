import fire
import uvicorn
from fastapi import FastAPI
from memory_api.routers import characters, sessions


app = FastAPI()
app.include_router(characters.router)
app.include_router(sessions.router)


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
    fire.Fire(main)
