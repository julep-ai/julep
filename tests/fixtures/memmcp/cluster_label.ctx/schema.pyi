# AI-ANCHOR: schema: cluster label input variables
"""Input variables for the cluster label prompt."""

class MemberItem:
    """A representative item from a macrocluster."""

    name: str
    """Entity name or episode title/snippet."""

    content: str = ""
    """Short representative content snippet."""

    source_type: str
    """Source category, typically 'entity' or 'episode'."""

class Input:
    """Template variables passed to the cluster label prompt."""

    members: list[MemberItem]
    """Top representative members for the cluster."""

    member_count: int
    """Total number of members in the cluster."""
