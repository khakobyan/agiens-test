"""
Configuration management for OpenClaw deployment.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class DeploymentConfig:
    """Configuration for OpenClaw deployment."""

    # Deployment paths
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    openclaw_home: Path = field(default_factory=lambda: Path.home() / '.openclaw')
    workspace_dir: Path = field(default_factory=lambda: Path.home() / 'openclaw' / 'workspace')

    # Docker settings
    image_name: str = "openclaw:local"
    container_name: str = "openclaw-gateway"
    gateway_port: int = 18789
    openclaw_version: str = "latest"

    # Gateway settings
    gateway_token: Optional[str] = None
    gateway_bind: str = "lan"

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_ai_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None

    # Build settings
    apt_packages: str = ""
    home_volume: str = "openclaw-home"

    # Deployment settings
    restart_policy: str = "unless-stopped"
    read_only: bool = True
    tmpfs_size: str = "512M"
    log_max_size: str = "10m"
    log_max_file: str = "3"

    # Health check settings
    health_interval: int = 30
    health_timeout: int = 10
    health_start_period: int = 60
    health_retries: int = 3

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.project_dir, str):
            self.project_dir = Path(self.project_dir)
        if isinstance(self.openclaw_home, str):
            self.openclaw_home = Path(self.openclaw_home)
        if isinstance(self.workspace_dir, str):
            self.workspace_dir = Path(self.workspace_dir)

    def to_env_dict(self) -> Dict[str, str]:
        """Convert config to environment variables dictionary."""
        env = {}

        if self.gateway_token:
            env['OPENCLAW_GATEWAY_TOKEN'] = self.gateway_token
        if self.gateway_bind:
            env['OPENCLAW_GATEWAY_BIND'] = self.gateway_bind
        if self.anthropic_api_key:
            env['ANTHROPIC_API_KEY'] = self.anthropic_api_key
        if self.openai_api_key:
            env['OPENAI_API_KEY'] = self.openai_api_key
        if self.google_ai_api_key:
            env['GOOGLE_AI_API_KEY'] = self.google_ai_api_key
        if self.ollama_base_url:
            env['OLLAMA_BASE_URL'] = self.ollama_base_url
        if self.apt_packages:
            env['OPENCLAW_DOCKER_APT_PACKAGES'] = self.apt_packages
        if self.home_volume:
            env['OPENCLAW_HOME_VOLUME'] = self.home_volume

        return env

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        data = asdict(self)
        # Convert Path objects to strings
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeploymentConfig':
        """Create config from dictionary."""
        return cls(**data)

    @classmethod
    def from_yaml(cls, path: Path) -> 'DeploymentConfig':
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env_file(cls, env_file: Path) -> 'DeploymentConfig':
        """Load configuration from .env file."""
        config = cls()

        if not env_file.exists():
            return config

        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Map environment variables to config attributes
                env_map = {
                    'OPENCLAW_GATEWAY_TOKEN': 'gateway_token',
                    'OPENCLAW_GATEWAY_BIND': 'gateway_bind',
                    'ANTHROPIC_API_KEY': 'anthropic_api_key',
                    'OPENAI_API_KEY': 'openai_api_key',
                    'GOOGLE_AI_API_KEY': 'google_ai_api_key',
                    'OLLAMA_BASE_URL': 'ollama_base_url',
                    'OPENCLAW_DOCKER_APT_PACKAGES': 'apt_packages',
                    'OPENCLAW_HOME_VOLUME': 'home_volume',
                }

                if key in env_map and value:
                    setattr(config, env_map[key], value)

        return config

    def save_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False)

    def save_env_file(self, path: Path) -> None:
        """Save configuration to .env file."""
        env_dict = self.to_env_dict()

        with open(path, 'w') as f:
            f.write("# OpenClaw Docker Configuration\n")
            f.write("# Generated by openclaw-deploy CLI\n\n")

            for key, value in env_dict.items():
                f.write(f"{key}={value}\n")


def load_config(
    config_file: Optional[Path] = None,
    env_file: Optional[Path] = None,
    **overrides
) -> DeploymentConfig:
    """
    Load configuration from file or environment.

    Args:
        config_file: Path to YAML config file
        env_file: Path to .env file
        **overrides: Additional config overrides

    Returns:
        DeploymentConfig instance
    """
    # Start with default config
    if config_file and config_file.exists():
        config = DeploymentConfig.from_yaml(config_file)
    elif env_file and env_file.exists():
        config = DeploymentConfig.from_env_file(env_file)
    else:
        config = DeploymentConfig()

    # Apply overrides
    for key, value in overrides.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)

    return config
