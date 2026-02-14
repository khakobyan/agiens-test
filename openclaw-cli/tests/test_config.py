"""
Tests for configuration module.
"""

import pytest
import tempfile
from pathlib import Path
from openclaw_deploy.config import DeploymentConfig, load_config


class TestDeploymentConfig:
    """Tests for DeploymentConfig class."""

    def test_default_config(self):
        """Test creating default configuration."""
        config = DeploymentConfig()

        assert config.image_name == "openclaw:local"
        assert config.container_name == "openclaw-gateway"
        assert config.gateway_port == 18789
        assert config.gateway_bind == "lan"
        assert config.openclaw_version == "latest"

    def test_config_with_custom_values(self):
        """Test creating configuration with custom values."""
        config = DeploymentConfig(
            image_name="custom:latest",
            gateway_port=8080,
            gateway_token="test-token-123"
        )

        assert config.image_name == "custom:latest"
        assert config.gateway_port == 8080
        assert config.gateway_token == "test-token-123"

    def test_to_env_dict(self):
        """Test converting config to environment dictionary."""
        config = DeploymentConfig(
            gateway_token="test-token",
            anthropic_api_key="sk-ant-test",
            openai_api_key="sk-test"
        )

        env_dict = config.to_env_dict()

        assert env_dict['OPENCLAW_GATEWAY_TOKEN'] == "test-token"
        assert env_dict['ANTHROPIC_API_KEY'] == "sk-ant-test"
        assert env_dict['OPENAI_API_KEY'] == "sk-test"

    def test_to_env_dict_excludes_none_values(self):
        """Test that None values are excluded from env dict."""
        config = DeploymentConfig(gateway_token="test")

        env_dict = config.to_env_dict()

        # Should have token but not API keys (which are None)
        assert 'OPENCLAW_GATEWAY_TOKEN' in env_dict
        assert 'ANTHROPIC_API_KEY' not in env_dict
        assert 'OPENAI_API_KEY' not in env_dict

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = DeploymentConfig(
            gateway_token="test-token",
            gateway_port=9000,
            image_name="test:latest"
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = DeploymentConfig.from_dict(data)

        assert restored.gateway_token == original.gateway_token
        assert restored.gateway_port == original.gateway_port
        assert restored.image_name == original.image_name

    def test_save_and_load_env_file(self):
        """Test saving and loading .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'

            config = DeploymentConfig(
                gateway_token="test-token-123",
                anthropic_api_key="sk-ant-test"
            )

            # Save to file
            config.save_env_file(env_file)
            assert env_file.exists()

            # Load from file
            loaded = DeploymentConfig.from_env_file(env_file)
            assert loaded.gateway_token == "test-token-123"
            assert loaded.anthropic_api_key == "sk-ant-test"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_with_defaults(self):
        """Test loading config with default values."""
        config = load_config()

        assert isinstance(config, DeploymentConfig)
        assert config.image_name == "openclaw:local"

    def test_load_config_with_overrides(self):
        """Test loading config with overrides."""
        config = load_config(
            gateway_token="override-token",
            gateway_port=7000
        )

        assert config.gateway_token == "override-token"
        assert config.gateway_port == 7000

    def test_load_config_from_env_file(self):
        """Test loading config from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'

            # Create .env file
            env_file.write_text("""
OPENCLAW_GATEWAY_TOKEN=file-token
ANTHROPIC_API_KEY=sk-ant-file
OPENCLAW_GATEWAY_BIND=localhost
""")

            config = load_config(env_file=env_file)

            assert config.gateway_token == "file-token"
            assert config.anthropic_api_key == "sk-ant-file"
            assert config.gateway_bind == "localhost"
