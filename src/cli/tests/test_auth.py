from pathlib import Path
from unittest.mock import patch

from julep_cli import app
from typer.testing import CliRunner


def create_runner(env: dict | None = None):
    env = env or {}
    return CliRunner(env=env)


mock_config_dir = Path("/tmp/mock/.config/julep")


def test_auth_command_should_save_api_key_when_provided_via_command_line():
    test_api_key = "test-api-key-123"

    runner = create_runner()

    with (
        patch("julep_cli.auth.save_config") as mock_save,
        patch("julep_cli.auth.get_julep_client") as mock_client,
        patch("julep_cli.auth.get_config") as mock_get_config,
    ):
        # Mock config to return empty dict
        mock_get_config.return_value = {}
        # Mock the client to simulate successful authentication
        mock_client.return_value.agents.list.return_value = []

        result = runner.invoke(
            app,
            ["auth", "--api-key", test_api_key, "--environment", "production", "--no-verify"],
        )

        assert result.exit_code == 0
        assert "Successfully authenticated with production environment!" in result.stdout
        mock_save.assert_called_once_with({
            "environment": "production",
            "api_key": test_api_key,
        })


def test_auth_command_should_use_api_key_from_environment_if_not_provided():
    test_api_key = "test-env-api-key-456"

    runner = create_runner({"JULEP_API_KEY": test_api_key})

    with (
        patch("julep_cli.auth.save_config") as mock_save,
        patch("julep_cli.auth.get_julep_client") as mock_client,
        patch("julep_cli.auth.get_config") as mock_get_config,
    ):
        # Mock config to return empty dict
        mock_get_config.return_value = {}
        # Mock the client to simulate successful authentication
        mock_client.return_value.agents.list.return_value = []

        result = runner.invoke(app, ["auth", "--environment", "production", "--no-verify"])

        assert result.exit_code == 0
        assert "Successfully authenticated with production environment!" in result.stdout
        mock_save.assert_called_once_with({
            "environment": "production",
            "api_key": test_api_key,
        })


def test_auth_command_should_fail_when_no_api_key_is_provided():
    runner = create_runner()

    with patch("julep_cli.auth.get_config") as mock_get_config:
        # Mock config to return empty dict
        mock_get_config.return_value = {}

        result = runner.invoke(app, ["auth", "--environment", "production"])

        # Typer exits with code 2 for missing required options when using the CLI runner
        assert result.exit_code == 2
        assert "Error" in result.stderr or "Missing option" in result.stderr


def test_auth_command_with_environment_dev():
    test_api_key = "test-dev-key-789"

    runner = create_runner()

    with (
        patch("julep_cli.auth.save_config") as mock_save,
        patch("julep_cli.auth.get_julep_client") as mock_client,
        patch("julep_cli.auth.get_config") as mock_get_config,
    ):
        # Mock config to return empty dict
        mock_get_config.return_value = {}
        # Mock the client to simulate successful authentication
        mock_client.return_value.agents.list.return_value = []

        result = runner.invoke(
            app, ["auth", "--api-key", test_api_key, "--environment", "dev", "--no-verify"]
        )

        assert result.exit_code == 0
        assert "Successfully authenticated with dev environment!" in result.stdout
        mock_save.assert_called_once_with({"environment": "dev", "api_key": test_api_key})


def test_auth_command_with_verification():
    test_api_key = "test-verify-key-101"

    runner = create_runner()

    with (
        patch("julep_cli.auth.save_config") as mock_save,
        patch("julep_cli.auth.get_julep_client") as mock_client,
        patch("julep_cli.auth.get_config") as mock_get_config,
    ):
        # Mock config to return empty dict
        mock_get_config.return_value = {}
        # Mock the client to simulate successful authentication
        mock_client.return_value.agents.list.return_value = []

        result = runner.invoke(
            app, ["auth", "--api-key", test_api_key, "--environment", "production"]
        )

        assert result.exit_code == 0
        assert "Successfully authenticated with production environment!" in result.stdout
        assert "Verifying API key" in result.stdout  # Progress spinner text
        mock_save.assert_called_once_with({
            "environment": "production",
            "api_key": test_api_key,
        })


def test_auth_command_verification_fails():
    # Use a valid JWT format for testing
    test_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    runner = create_runner()

    with (
        patch("julep_cli.auth.get_julep_client") as mock_client,
        patch("julep_cli.auth.get_config") as mock_get_config,
    ):
        # Mock config to return empty dict
        mock_get_config.return_value = {}
        # Mock the client to simulate failed authentication
        mock_client.return_value.agents.list.side_effect = Exception("Invalid API key")

        result = runner.invoke(
            app, ["auth", "--api-key", test_api_key, "--environment", "production"]
        )

        assert result.exit_code == 1
        assert "Error verifying API key" in result.stderr


def test_auth_command_invalid_jwt_format():
    invalid_api_key = "not-a-jwt"

    runner = create_runner()

    with patch("julep_cli.auth.get_config") as mock_get_config:
        # Mock config to return empty dict
        mock_get_config.return_value = {}

        # Since the validation is done inside the command through the wrapper's prompting,
        # and 'not-a-jwt' is not a valid JWT, the command will fail validation
        result = runner.invoke(
            app, ["auth", "--api-key", invalid_api_key, "--environment", "production"]
        )

        # The JWT validation happens during verification
        assert result.exit_code == 1
        assert (
            "Error verifying API key" in result.stderr
            and "invalid token format" in result.stderr
        )
