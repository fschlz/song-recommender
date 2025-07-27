"""
Configuration management using pydantic-settings for the DJ AI Assistant.

This module provides centralized configuration management with environment
variable support, type validation, and default values.
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude models"
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="DEBUG",
        description="Logging level for the application"
    )

    # Application Configuration
    mock_mode: bool = Field(
        default=False,
        description="Enable mock mode for testing without API calls"
    )

    # AI Model Configuration
    default_model: str = Field(
        default="claude-3-5-sonnet-20240620",
        description="Default Anthropic model to use for recommendations"
    )

    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for AI responses"
    )

    # Application Limits
    max_recommendations: int = Field(
        default=10,
        description="Maximum number of recommendations allowed per request"
    )

    min_recommendations: int = Field(
        default=1,
        description="Minimum number of recommendations per request"
    )

    # Streamlit Configuration
    streamlit_port: int = Field(
        default=8501,
        description="Port for Streamlit application"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }

    @property
    def effective_api_key(self) -> str:
        """
        Get the effective API key from environment variables or .env file.
        
        Returns:
            str: The effective API key to use
        """
        return self.anthropic_api_key

    @property
    def is_api_key_configured(self) -> bool:
        """
        Check if API key is properly configured.
        
        Returns:
            bool: True if API key is available, False otherwise
        """
        return bool(self.effective_api_key)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings: The application settings
    """
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment and configuration files.
    
    Returns:
        Settings: The reloaded settings instance
    """
    global settings
    settings = Settings()
    return settings
