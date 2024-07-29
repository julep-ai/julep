# /usr/bin/env python3

MIGRATION_ID = "developers_relation"
CREATED_AT = 1721666295.486804


def up(client):
    client.run(
        """
    # Create developers table and insert default developer
    ?[developer_id, email] <- [
        ["00000000-0000-0000-0000-000000000000", "developers@example.com"]
    ]

    :create developers {
        developer_id: Uuid,
        =>
        email: String,
        active: Bool default true,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """
    )


def down(client):
    client.run(
        """
    ::remove developers
    """
    )
