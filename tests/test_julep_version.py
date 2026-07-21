from importlib.metadata import version

from typer.testing import CliRunner

from julep.cli.main import app


def test_version_matches_package() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("julep") in result.output
