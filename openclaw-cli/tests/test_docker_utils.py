"""
Tests for docker_utils module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from openclaw_deploy.docker_utils import (
    check_container_exists,
    check_container_running,
    get_container_status,
    get_container_health,
    run_command,
    DockerError
)
from openclaw_deploy.config import DeploymentConfig


class TestRunCommand:
    """Tests for run_command function."""

    @patch('openclaw_deploy.docker_utils.subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(returncode=0, stdout='output', stderr='')

        result = run_command(['echo', 'test'])

        assert result.returncode == 0
        assert result.stdout == 'output'
        mock_run.assert_called_once()

    @patch('openclaw_deploy.docker_utils.subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test command execution failure."""
        mock_run.return_value = Mock(returncode=1, stdout='', stderr='error')

        with pytest.raises(DockerError):
            run_command(['false'])

    @patch('openclaw_deploy.docker_utils.subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(['sleep'], 1)

        with pytest.raises(DockerError) as exc_info:
            run_command(['sleep', '10'], timeout=1)

        assert 'timed out' in str(exc_info.value).lower()


class TestContainerChecks:
    """Tests for container status check functions."""

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_check_container_exists_true(self, mock_run):
        """Test checking if container exists (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='openclaw-gateway\n')

        result = check_container_exists('openclaw-gateway')
        assert result is True

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_check_container_exists_false(self, mock_run):
        """Test checking if container exists (false case)."""
        mock_run.return_value = Mock(returncode=0, stdout='')

        result = check_container_exists('openclaw-gateway')
        assert result is False

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_check_container_running_true(self, mock_run):
        """Test checking if container is running (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='openclaw-gateway\n')

        result = check_container_running('openclaw-gateway')
        assert result is True

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_get_container_status(self, mock_run):
        """Test getting container status."""
        mock_run.return_value = Mock(returncode=0, stdout='running\n')

        status = get_container_status('openclaw-gateway')
        assert status == 'running'

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_get_container_health_healthy(self, mock_run):
        """Test getting container health status."""
        mock_run.return_value = Mock(returncode=0, stdout='healthy\n')

        health = get_container_health('openclaw-gateway')
        assert health == 'healthy'

    @patch('openclaw_deploy.docker_utils.run_command')
    def test_get_container_health_no_healthcheck(self, mock_run):
        """Test getting health when no healthcheck is defined."""
        mock_run.return_value = Mock(returncode=0, stdout='<no value>\n')

        health = get_container_health('openclaw-gateway')
        assert health is None


class TestDeploymentInfo:
    """Tests for deployment information functions."""

    @patch('openclaw_deploy.docker_utils.check_container_exists')
    @patch('openclaw_deploy.docker_utils.check_container_running')
    @patch('openclaw_deploy.docker_utils.get_container_status')
    @patch('openclaw_deploy.docker_utils.get_container_health')
    def test_get_deployment_info(
        self, mock_health, mock_status, mock_running, mock_exists
    ):
        """Test getting deployment information."""
        from openclaw_deploy.docker_utils import get_deployment_info

        mock_exists.return_value = True
        mock_running.return_value = True
        mock_status.return_value = 'running'
        mock_health.return_value = 'healthy'

        config = DeploymentConfig(
            gateway_token='test-token',
            gateway_port=18789
        )

        info = get_deployment_info(config)

        assert info['container_exists'] is True
        assert info['container_running'] is True
        assert info['container_status'] == 'running'
        assert info['container_health'] == 'healthy'
        assert 'gateway_url' in info
        assert 'gateway_url_with_token' in info
