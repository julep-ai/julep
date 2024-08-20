import re

import yaml
from fastapi import Request


class YamlMiddleware:
    def __init__(self, path_regex: str = r".*"):
        self.path_regex = re.compile(path_regex)

    async def __call__(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "").strip().lower()

        # Filter out requests that are not for YAML and not for the specified path
        if not self.path_regex.match(request.url.path) or content_type not in [
            "application/x-yaml",
            "application/yaml",
            "text/yaml",
            "text/x-yaml",
        ]:
            return await call_next(request)

        # Parse the YAML body into a Python object
        body = yaml.load(await request.body(), yaml.CSafeLoader)
        request._json = body

        # Switch headers to JSON
        headers = request.headers.mutablecopy()
        headers["content-type"] = "application/json"

        request._headers = headers

        # Continue processing the request
        response = await call_next(request)
        return response
