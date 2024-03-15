import json
from uuid import UUID


def create_user_query(
    user_id: UUID, developer_id: UUID, name: str, about: str, metadata: dict = {}
):
    user_id = str(user_id)
    name = json.dumps(name)
    about = json.dumps(about)
    metadata = json.dumps(metadata)

    return f"""
    {{
        # Then create the user
        ?[user_id, developer_id, name, about, metadata] <- [
            [to_uuid("{user_id}"), to_uuid("{developer_id}"), {name}, {about}, {metadata}]
        ]

        :insert users {{
            developer_id,
            user_id =>
            name,
            about,
            metadata,
        }}
        :returning
    }}"""
