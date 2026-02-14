"""
Tests for validators module.
"""

import pytest
from pathlib import Path
from openclaw_deploy.validators import (
    check_command_exists,
    check_docker_installed,
    check_docker_compose,
    check_port_available,
    check_disk_space,
    validate_all_prerequisites
)


class TestCommandChecks:
    """Tests for command existence checks."""

    def test_check_command_exists_valid(self):
        """Test checking for a command that exists."""
        # 'ls' should exist on all systems
        assert check_command_exists('ls') is True
        assert check_command_exists('sh') is True

    def test_check_command_exists_invalid(self):
        """Test checking for a command that doesn't exist."""
        assert check_command_exists('nonexistent_command_12345') is False


class TestDockerChecks:
    """Tests for Docker-related checks."""

    def test_check_docker_installed(self):
        """Test Docker installation check."""
        success, message = check_docker_installed()
        assert isinstance(success, bool)
        assert isinstance(message, str)
        assert len(message) > 0

    def test_check_docker_compose(self):
        """Test Docker Compose check."""
        success, message = check_docker_compose()
        assert isinstance(success, bool)
        assert isinstance(message, str)
        assert len(message) > 0


class TestPortChecks:
    """Tests for port availability checks."""

    def test_check_port_available_high_port(self):
        """Test checking a high port number that should be available."""
        # Port 54321 should typically be available
        success, message = check_port_available(54321)
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_check_port_message_format(self):
        """Test that port check returns properly formatted message."""
        success, message = check_port_available(12345)
        assert 'port' in message.lower() or '12345' in message


class TestDiskSpaceChecks:
    """Tests for disk space checks."""

    def test_check_disk_space_current_dir(self):
        """Test disk space check on current directory."""
        success, message = check_disk_space(Path.cwd(), required_gb=0.1)
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_check_disk_space_excessive_requirement(self):
        """Test disk space check with excessive requirement."""
        # Require 1000 TB - should fail
        success, message = check_disk_space(Path.cwd(), required_gb=1000000)
        assert success is False
        assert 'insufficient' in message.lower() or 'available' in message.lower()


class TestValidateAll:
    """Tests for comprehensive validation."""

    def test_validate_all_prerequisites_returns_list(self):
        """Test that validate_all returns a list of tuples."""
        results = validate_all_prerequisites()
        assert isinstance(results, list)
        assert len(results) > 0

        for check_name, success, message in results:
            assert isinstance(check_name, str)
            assert isinstance(success, bool)
            assert isinstance(message, str)

    def test_validate_all_prerequisites_has_required_checks(self):
        """Test that all required checks are included."""
        results = validate_all_prerequisites()
        check_names = [name for name, _, _ in results]

        required_checks = [
            'Docker Installed',
            'Docker Compose',
            'Port Available',
            'Disk Space'
        ]

        for required_check in required_checks:
            assert any(required_check in name for name in check_names), \
                f"Required check '{required_check}' not found in validation results"
