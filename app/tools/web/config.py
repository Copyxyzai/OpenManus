"""
Configuration Loader for Perplexity Tools

Loads configuration from perplexity.toml file.
"""

import os
from pathlib import Path
from typing import Any, Dict

import toml

from app.logger import logger


class PerplexityConfig:
    """Configuration for Per plexity search tools"""

    _instance = None
    _config: Dict[str, Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from TOML file"""
        config_path = Path(__file__).parent.parent.parent / "config" / "perplexity.toml"

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    self._config = toml.load(f)
                logger.info(f"✅ Loaded Perplexity config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                self._config = self._get_defaults()
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self._config = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "search": {
                "default_num_results": 5,
                "max_num_results": 10,
                "cache_ttl": 3600,
                "cache_max_size": 100,
            },
            "deep_search": {
                "max_sources": 10,
                "standard_max_chars": 3000,
                "comprehensive_max_chars": 8000,
                "scraping_timeout": 30,
            },
            "rate_limit": {
                "max_calls_per_hour": 50,
                "period_seconds": 3600,
            },
            "engines": {
                "primary": "duckduckgo",
                "fallbacks": ["bing_fallback"],
            },
            "retry": {
                "max_attempts": 3,
                "min_wait": 4,
                "max_wait": 10,
            },
            "sanitization": {
                "max_query_length": 500,
                "min_query_length": 2,
            },
        }

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            section: Config section name
            key: Config key
            default: Default value if not found

        Returns:
            Configuration value
        """
        if self._config is None:
            self._load_config()

        return self._config.get(section, {}).get(key, default)

    @property
    def search(self) -> Dict[str, Any]:
        """Get search configuration"""
        return self._config.get("search", {})

    @property
    def deep_search(self) -> Dict[str, Any]:
        """Get deep search configuration"""
        return self._config.get("deep_search", {})

    @property
    def rate_limit(self) -> Dict[str, Any]:
        """Get rate limit configuration"""
        return self._config.get("rate_limit", {})

    @property
    def engines(self) -> Dict[str, Any]:
        """Get search engines configuration"""
        return self._config.get("engines", {})

    @property
    def retry(self) -> Dict[str, Any]:
        """Get retry configuration"""
        return self._config.get("retry", {})

    @property
    def sanitization(self) -> Dict[str, Any]:
        """Get sanitization configuration"""
        return self._config.get("sanitization", {})


# Global config instance
perplexity_config = PerplexityConfig()
