import uvicorn

from .env import host, port, backlog
from .web import create_app

TIMEOUT_KEEP_ALIVE = 30  # seconds.

if __name__ == "__main__":
    app = create_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
        backlog=backlog,
    )
