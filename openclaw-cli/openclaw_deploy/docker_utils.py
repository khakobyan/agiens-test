"""
Docker operations for OpenClaw deployment.
"""

import subprocess
import time
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from .config import DeploymentConfig


logger = logging.getLogger(__name__)


class DockerError(Exception):
    """Raised when Docker operations fail."""
    pass


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    timeout: Optional[int] = None,
    check: bool = True
) -> subprocess.CompletedProcess:
    """
    Run a shell command with proper error handling.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        env: Environment variables
        capture_output: Capture stdout/stderr
        timeout: Command timeout in seconds
        check: Raise exception on non-zero exit code

    Returns:
        CompletedProcess instance

    Raises:
        DockerError on failure
    """
    try:
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False
        )

        if check and result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise DockerError(f"Command failed: {' '.join(cmd)}\n{error_msg}")

        return result
    except subprocess.TimeoutExpired as e:
        raise DockerError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    except Exception as e:
        raise DockerError(f"Command execution error: {e}")


def check_container_exists(container_name: str) -> bool:
    """Check if a container exists."""
    try:
        result = run_command(
            ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
            check=False
        )
        return container_name in result.stdout
    except Exception:
        return False


def check_container_running(container_name: str) -> bool:
    """Check if a container is running."""
    try:
        result = run_command(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
            check=False
        )
        return container_name in result.stdout
    except Exception:
        return False


def get_container_status(container_name: str) -> Optional[str]:
    """Get container status."""
    try:
        result = run_command(
            ['docker', 'inspect', '--format', '{{.State.Status}}', container_name],
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_container_health(container_name: str) -> Optional[str]:
    """Get container health status."""
    try:
        result = run_command(
            ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container_name],
            check=False
        )
        if result.returncode == 0:
            health = result.stdout.strip()
            return health if health and health != '<no value>' else None
    except Exception:
        pass
    return None


def create_directories(config: DeploymentConfig) -> None:
    """Create required host directories."""
    logger.info("Creating host directories...")

    directories = [
        config.openclaw_home,
        config.workspace_dir,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {directory}")

    logger.info(f"✓ Directories created: {config.openclaw_home}, {config.workspace_dir}")


def generate_env_file(config: DeploymentConfig) -> None:
    """Generate .env file from configuration."""
    env_file = config.project_dir / '.env'

    logger.info(f"Generating environment file: {env_file}")

    # Generate token if not provided
    if not config.gateway_token:
        import secrets
        config.gateway_token = secrets.token_hex(32)
        logger.info("Generated new gateway token")

    config.save_env_file(env_file)
    logger.info(f"✓ Environment file created: {env_file}")


def build_image(config: DeploymentConfig, no_cache: bool = False) -> None:
    """
    Build Docker image.

    Args:
        config: Deployment configuration
        no_cache: Build without cache
    """
    logger.info(f"Building Docker image: {config.image_name}")
    logger.info("This may take several minutes on first build...")

    cmd = ['docker', 'compose', '-f', str(config.project_dir / 'docker-compose.yml'), 'build']

    if no_cache:
        cmd.append('--no-cache')

    # Set environment for build args
    env = {**subprocess.os.environ, **config.to_env_dict()}

    result = run_command(cmd, cwd=config.project_dir, env=env, timeout=1200)

    logger.info(f"✓ Docker image built successfully: {config.image_name}")


def start_services(config: DeploymentConfig) -> None:
    """Start Docker services."""
    logger.info("Starting OpenClaw services...")

    env = {**subprocess.os.environ, **config.to_env_dict()}

    cmd = [
        'docker', 'compose',
        '-f', str(config.project_dir / 'docker-compose.yml'),
        'up', '-d'
    ]

    run_command(cmd, cwd=config.project_dir, env=env, timeout=120)

    logger.info("✓ Services started successfully")


def stop_services(config: DeploymentConfig, remove_volumes: bool = False) -> None:
    """
    Stop Docker services.

    Args:
        config: Deployment configuration
        remove_volumes: Remove volumes when stopping
    """
    logger.info("Stopping OpenClaw services...")

    env = {**subprocess.os.environ, **config.to_env_dict()}

    cmd = [
        'docker', 'compose',
        '-f', str(config.project_dir / 'docker-compose.yml'),
        'down'
    ]

    if remove_volumes:
        cmd.append('-v')

    run_command(cmd, cwd=config.project_dir, env=env, timeout=60)

    logger.info("✓ Services stopped successfully")


def restart_services(config: DeploymentConfig) -> None:
    """Restart Docker services."""
    logger.info("Restarting OpenClaw services...")

    env = {**subprocess.os.environ, **config.to_env_dict()}

    cmd = [
        'docker', 'compose',
        '-f', str(config.project_dir / 'docker-compose.yml'),
        'restart'
    ]

    run_command(cmd, cwd=config.project_dir, env=env, timeout=120)

    logger.info("✓ Services restarted successfully")


def configure_openclaw(config: DeploymentConfig) -> None:
    """
    Configure OpenClaw gateway with local mode and auth token.

    Args:
        config: Deployment configuration

    Raises:
        DockerError on failure
    """
    logger.info("Configuring OpenClaw gateway...")

    # Set gateway mode to local
    logger.debug("Setting gateway.mode to local")
    cmd_mode = [
        'docker', 'run', '--rm',
        '-v', f'{config.openclaw_home}:/home/node/.openclaw',
        f'{config.image_name}',
        'node', 'dist/index.js', 'config', 'set', 'gateway.mode', 'local'
    ]
    run_command(cmd_mode, timeout=30)
    logger.debug("✓ Gateway mode set to local")

    # Set auth token if provided
    if config.gateway_token:
        logger.debug("Setting gateway auth token")
        cmd_token = [
            'docker', 'run', '--rm',
            '-v', f'{config.openclaw_home}:/home/node/.openclaw',
            f'{config.image_name}',
            'node', 'dist/index.js', 'config', 'set', 'gateway.auth.token', config.gateway_token
        ]
        run_command(cmd_token, timeout=30)
        logger.debug("✓ Gateway auth token configured")

    # Restart gateway to apply configuration
    logger.debug("Restarting gateway to apply configuration")
    env = {**subprocess.os.environ, **config.to_env_dict()}
    cmd_restart = [
        'docker', 'compose',
        '-f', str(config.project_dir / 'docker-compose.yml'),
        'restart', 'openclaw-gateway'
    ]
    run_command(cmd_restart, cwd=config.project_dir, env=env, timeout=60)
    logger.debug("✓ Gateway restarted")

    logger.info("✓ OpenClaw configuration completed")


def wait_for_healthy(
    container_name: str,
    timeout: int = 120,
    interval: int = 5
) -> bool:
    """
    Wait for container to become healthy.

    Args:
        container_name: Container name
        timeout: Maximum wait time in seconds
        interval: Check interval in seconds

    Returns:
        True if container became healthy
    """
    logger.info(f"Waiting for {container_name} to become healthy...")

    start_time = time.time()
    retries = 0

    while time.time() - start_time < timeout:
        status = get_container_status(container_name)
        health = get_container_health(container_name)

        logger.debug(f"Container status: {status}, health: {health}")

        if status == 'running':
            if health == 'healthy':
                elapsed = int(time.time() - start_time)
                logger.info(f"✓ Container is healthy (took {elapsed}s)")
                return True
            elif health == 'unhealthy':
                logger.warning(f"Container is unhealthy")
                return False
            # If no health check, just check if running
            elif health is None and retries > 3:
                logger.info(f"✓ Container is running (no health check)")
                return True
        elif status in ['exited', 'dead']:
            logger.error(f"Container exited unexpectedly: {status}")
            return False

        retries += 1
        time.sleep(interval)

    logger.warning(f"Container did not become healthy within {timeout}s")
    return False


def get_logs(config: DeploymentConfig, tail: int = 50, follow: bool = False) -> None:
    """
    Get container logs.

    Args:
        config: Deployment configuration
        tail: Number of lines to show
        follow: Follow log output
    """
    env = {**subprocess.os.environ, **config.to_env_dict()}

    cmd = [
        'docker', 'compose',
        '-f', str(config.project_dir / 'docker-compose.yml'),
        'logs', '--tail', str(tail)
    ]

    if follow:
        cmd.append('-f')

    cmd.append('openclaw-gateway')

    run_command(cmd, cwd=config.project_dir, env=env, capture_output=False, check=False)


def remove_container(container_name: str, force: bool = False) -> None:
    """Remove a container."""
    if not check_container_exists(container_name):
        return

    logger.info(f"Removing container: {container_name}")

    cmd = ['docker', 'rm', container_name]
    if force:
        cmd.insert(2, '-f')

    run_command(cmd, check=False)

    logger.info(f"✓ Container removed: {container_name}")


def remove_image(image_name: str, force: bool = False) -> None:
    """Remove a Docker image."""
    logger.info(f"Removing image: {image_name}")

    cmd = ['docker', 'rmi', image_name]
    if force:
        cmd.insert(2, '-f')

    result = run_command(cmd, check=False)

    if result.returncode == 0:
        logger.info(f"✓ Image removed: {image_name}")
    else:
        logger.warning(f"Could not remove image: {image_name}")


def remove_volume(volume_name: str, force: bool = False) -> None:
    """Remove a Docker volume."""
    logger.info(f"Removing volume: {volume_name}")

    cmd = ['docker', 'volume', 'rm', volume_name]
    if force:
        cmd.insert(3, '-f')

    result = run_command(cmd, check=False)

    if result.returncode == 0:
        logger.info(f"✓ Volume removed: {volume_name}")
    else:
        logger.warning(f"Could not remove volume: {volume_name}")


def get_deployment_info(config: DeploymentConfig) -> Dict[str, any]:
    """
    Get deployment information.

    Returns:
        Dictionary with deployment status info
    """
    info = {
        'container_exists': check_container_exists(config.container_name),
        'container_running': check_container_running(config.container_name),
        'container_status': get_container_status(config.container_name),
        'container_health': get_container_health(config.container_name),
        'gateway_url': f"http://localhost:{config.gateway_port}",
    }

    if config.gateway_token:
        info['gateway_url_with_token'] = f"http://localhost:{config.gateway_port}?token={config.gateway_token}"

    return info
