from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from ..env import api_key, api_key_header_name

api_key_header = APIKeyHeader(name=api_key_header_name, auto_error=False)


async def get_api_key(user_api_key: str = Security(api_key_header)):
    user_api_key = (user_api_key or "").replace("Bearer ", "").strip()

    if user_api_key != api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )
    else:
        return user_api_key
