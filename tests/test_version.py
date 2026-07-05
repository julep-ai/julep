from importlib.metadata import version


def test_version_matches_distribution_metadata() -> None:
    import julep

    # __version__ must be derived from the installed distribution, never a hardcoded
    # constant (the stale-wheel bug reported 0.1.0 against a 1.0.0rc1 distribution).
    assert julep.__version__ == version("julep")
    assert julep.__version__ != "0.1.0"
