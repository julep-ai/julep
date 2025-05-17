import base64

from agents_api.routers.files.create_file import upload_file_content
from agents_api.routers.files.get_file import fetch_file_content
from uuid_extensions import uuid7
from ward import test


@test("streaming upload and download roundtrip")
async def _(s3_client=s3_client):
    data = b"streaming test" * 1024
    encoded = base64.b64encode(data).decode()
    file_id = uuid7()

    await upload_file_content(file_id, encoded)
    result = await fetch_file_content(file_id)

    assert result == encoded
