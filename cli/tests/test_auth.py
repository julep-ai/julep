from pathlib import Path
from unittest.mock import patch

from julep_cli import app
from typer.testing import CliRunner
from ward import test


def create_runner(env: dict | None = None):
    env = env or {}
    return CliRunner(env=env)


mock_config_dir = Path("/tmp/mock/.config/julep")


@test("auth command should save API key when provided via command line")
def _():
    test_api_key = "test-api-key-123"

    runner = create_runner()

    with (
        patch("julep_cli.CONFIG_DIR", mock_config_dir),
        patch("julep_cli.save_config") as mock_save,
    ):
        result = runner.invoke(app, ["auth", "--api-key", test_api_key])

        assert result.exit_code == 0
        assert "Successfully authenticated!" in result.stdout
        mock_save.assert_called_once_with({"api_key": test_api_key})


@test("auth command should use API key from environment if not provided")
def _():
    test_api_key = "test-env-api-key-456"

    runner = create_runner({"JULEP_API_KEY": test_api_key})

    with (
        patch("julep_cli.CONFIG_DIR", mock_config_dir),
        patch("julep_cli.save_config") as mock_save,
    ):
        result = runner.invoke(app, ["auth"])

        assert result.exit_code == 0
        assert "Successfully authenticated!" in result.stdout
        mock_save.assert_called_once_with({"api_key": test_api_key})


@test("auth command should fail when no API key is provided")
def _():
    runner = create_runner()

    result = runner.invoke(app, ["auth"])

    assert result.exit_code == 1
    assert "No API key provided" in result.stdout


@test("auth command should prompt for API key if not provided and not in env")
def _():
    test_api_key = "test-prompt-key-789"

    runner = create_runner()

    with (
        patch("julep_cli.CONFIG_DIR", mock_config_dir),
        patch("julep_cli.save_config") as mock_save,
    ):
        result = runner.invoke(app, ["auth"], input=f"{test_api_key}\n")

        assert result.exit_code == 0
        assert "Successfully authenticated!" in result.stdout
        mock_save.assert_called_once_with({"api_key": test_api_key})
