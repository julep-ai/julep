"""Environment configuration for the Responses API."""

import os
from typing import Any, Dict, List, Optional, Union

from environs import Env

env = Env()
env.read_env()  # read .env file, if it exists


class Config:
    """Configuration for the Responses API."""

    # API settings
    DEBUG: bool = env.bool("RESPONSES_API_DEBUG", False)
    TESTING: bool = env.bool("RESPONSES_API_TESTING", False)
    ENV: str = env.str("RESPONSES_API_ENV", "development")
    LOG_LEVEL: str = env.str("RESPONSES_API_LOG_LEVEL", "INFO")
    
    # Server settings
    HOST: str = env.str("RESPONSES_API_HOST", "0.0.0.0")
    PORT: int = env.int("RESPONSES_API_PORT", 8080)
    
    # Database settings
    DATABASE_URL: str = env.str("RESPONSES_API_DATABASE_URL", "")
    
    # LLM settings
    OPENAI_API_KEY: str = env.str("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = env.str("RESPONSES_API_DEFAULT_MODEL", "gpt-4o")
    
    # Security settings
    API_KEY: str = env.str("RESPONSES_API_KEY", "")
    
    # Sentry settings
    SENTRY_DSN: Optional[str] = env.str("SENTRY_DSN", None)
    
    # Prometheus settings
    ENABLE_METRICS: bool = env.bool("RESPONSES_API_ENABLE_METRICS", False)
    
    # CORS settings
    CORS_ORIGINS: List[str] = env.list("RESPONSES_API_CORS_ORIGINS", ["*"])
    
    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and key.isupper()
        }


config = Config() 