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
            with open(config_path, "r") as f:
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
                api_key = api_key.split("/", 1)[1]
                return api_key

    return None