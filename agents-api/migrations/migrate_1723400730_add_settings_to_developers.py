# /usr/bin/env python3

MIGRATION_ID = "add_settings_to_developers"
CREATED_AT = 1723400730.539554


def up(client):
    client.run(
        """
    ?[
        developer_id,
        email,
        active,
        tags,
        settings,
        created_at,
        updated_at,
    ] := *developers {
            developer_id,
            email,
            active,
            created_at,
            updated_at,
        },
        tags = [],
        settings = {}

    :replace developers {
        developer_id: Uuid,
        =>
        email: String,
        active: Bool default true,
        tags: [String] default [],
        settings: Json,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """
    )


def down(client):
    client.run(
        """
    ?[
        developer_id,
        email,
        active,
        created_at,
        updated_at,
    ] := *developers {
            developer_id,
            email,
            active,
            created_at,
            updated_at,
        }

    :replace developers {
        developer_id: Uuid,
        =>
        email: String,
        active: Bool default true,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """
    )
