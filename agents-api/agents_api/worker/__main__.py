"""
This script initializes and runs a Temporal worker that listens for tasks on a specified queue.
It supports various workflows and activities related to agents' operations.
"""

#!/usr/bin/env python3

import asyncio

from .worker import create_worker


async def main():
    """
    Initializes the Temporal client and worker with TLS configuration (if provided),
    then starts the worker to listen for tasks on the configured task queue.
    """

    worker = await create_worker()

    # Start the worker to listen for and process tasks
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
