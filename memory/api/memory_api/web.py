import fire
import uvicorn
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from memory_api.routers import (
    characters, 
    sessions, 
    embedder, 
    users, 
    entries,
    models,
    personality,
    beliefs,
    episodes,
)


logger = logging.getLogger(__name__)


def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
        logger.exception(exc)
        content = {'status_code': 10422, 'message': exc_str, 'data': None}
        return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

register_exception(app)

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
    episodes.db.init()

    fire.Fire(main)
