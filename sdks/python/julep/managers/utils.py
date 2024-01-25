from uuid import UUID


def is_valid_uuid4(uuid_to_test: str) -> bool:
    """
    Check if uuid_to_test is a valid UUID v4.

    Parameters
    ----------
    uuid_to_test : str
    """

    if isinstance(uuid_to_test, UUID):
        return uuid_to_test.version == 4

    try:
        _ = UUID(uuid_to_test, version=4)
    except ValueError:
        return False

    return True
