from pathlib import Path

import yaml

config_path = Path("/app/litellm-config.yaml")

_config = None


def get_config():
    global _config
    if _config is None:
        if not config_path.exists():
            print(f"Warning: LiteLLM config file not found at {config_path}")
            return {}

        try:
            with open(config_path) as f:
                _config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading LiteLLM config: {e}")
            return {}

    return _config


def get_api_key_env_var_name(model: str) -> str | None:
    config = get_config()

    for model_config in config.get("model_list", []):
        if model_config.get("model_name") == model:
            api_key = model_config.get("litellm_params", {}).get("api_key")
            if api_key:
                return api_key.split("/", 1)[1]

    return None


def get_litellm_model_name(model: str) -> str:
    """
    Convert a model name to its LiteLLM equivalent by looking it up in the config.
    Returns the litellm_params.model value if found, otherwise returns the original model name.

    Examples:
        "gpt-4o" -> "openai/gpt-4o"
        "gemini-1.5-pro" -> "gemini/gemini-1.5-pro"
        "claude-3.5-sonnet" -> "claude-3-5-sonnet-20241022"
    """
    config = get_config()

    for model_config in config.get("model_list", []):
        if model_config.get("model_name") == model:
            litellm_model = model_config.get("litellm_params", {}).get("model")
            if litellm_model:
                return litellm_model

    # AIDEV-NOTE: If model not found in config, return original name
    return model
