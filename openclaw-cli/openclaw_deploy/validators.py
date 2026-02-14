"""
Prerequisite validation for OpenClaw deployment.
"""

import subprocess
import shutil
import logging
from typing import List, Tuple
from pathlib import Path


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def check_docker_installed() -> Tuple[bool, str]:
    """
    Check if Docker is installed.

    Returns:
        Tuple of (success, message)
    """
    if not check_command_exists('docker'):
        return False, "Docker is not installed. Install from https://docs.docker.com/get-docker/"

    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Docker found: {version}"
        else:
            return False, "Docker command failed"
    except Exception as e:
        return False, f"Error checking Docker: {e}"


def check_docker_compose() -> Tuple[bool, str]:
    """
    Check if Docker Compose V2 is available.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            ['docker', 'compose', 'version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Docker Compose found: {version}"
        else:
            return False, "Docker Compose V2 not available. Update Docker or install compose plugin."
    except Exception as e:
        return False, f"Error checking Docker Compose: {e}"


def check_docker_running() -> Tuple[bool, str]:
    """
    Check if Docker daemon is running.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "Docker daemon is running"
        else:
            return False, "Docker daemon is not running. Start Docker and try again."
    except subprocess.TimeoutExpired:
        return False, "Docker daemon check timed out"
    except Exception as e:
        return False, f"Error checking Docker daemon: {e}"


def check_docker_permissions() -> Tuple[bool, str]:
    """
    Check if user has Docker permissions.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "Docker permissions OK"
        elif 'permission denied' in result.stderr.lower():
            return False, "Permission denied. Add user to docker group or run with sudo."
        else:
            return False, f"Docker permissions check failed: {result.stderr}"
    except Exception as e:
        return False, f"Error checking Docker permissions: {e}"


def check_port_available(port: int) -> Tuple[bool, str]:
    """
    Check if a port is available.

    Args:
        port: Port number to check

    Returns:
        Tuple of (success, message)
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result == 0:
                return False, f"Port {port} is already in use"
            else:
                return True, f"Port {port} is available"
    except Exception as e:
        return False, f"Error checking port {port}: {e}"


def check_disk_space(path: Path, required_gb: float = 5.0) -> Tuple[bool, str]:
    """
    Check if sufficient disk space is available.

    Args:
        path: Path to check
        required_gb: Required space in GB

    Returns:
        Tuple of (success, message)
    """
    try:
        stat = shutil.disk_usage(path)
        available_gb = stat.free / (1024 ** 3)

        if available_gb >= required_gb:
            return True, f"Disk space OK: {available_gb:.2f} GB available"
        else:
            return False, f"Insufficient disk space: {available_gb:.2f} GB available, {required_gb} GB required"
    except Exception as e:
        return False, f"Error checking disk space: {e}"


def check_required_files(project_dir: Path) -> Tuple[bool, str]:
    """
    Check if required deployment files exist.

    Args:
        project_dir: Project directory

    Returns:
        Tuple of (success, message)
    """
    required_files = ['Dockerfile', 'docker-compose.yml', '.env.example']
    missing_files = []

    for file in required_files:
        if not (project_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        return False, f"Missing required files: {', '.join(missing_files)}"
    else:
        return True, "All required files present"


def validate_all_prerequisites(
    port: int = 18789,
    project_dir: Path = Path.cwd(),
    required_disk_gb: float = 5.0
) -> List[Tuple[str, bool, str]]:
    """
    Run all prerequisite checks.

    Args:
        port: Gateway port to check
        project_dir: Project directory
        required_disk_gb: Required disk space in GB

    Returns:
        List of (check_name, success, message) tuples
    """
    checks = [
        ("Docker Installed", *check_docker_installed()),
        ("Docker Compose", *check_docker_compose()),
        ("Docker Running", *check_docker_running()),
        ("Docker Permissions", *check_docker_permissions()),
        ("Port Available", *check_port_available(port)),
        ("Disk Space", *check_disk_space(project_dir, required_disk_gb)),
        ("Required Files", *check_required_files(project_dir)),
    ]

    return checks


def validate_and_report(
    port: int = 18789,
    project_dir: Path = Path.cwd(),
    required_disk_gb: float = 5.0,
    strict: bool = True
) -> bool:
    """
    Validate prerequisites and report results.

    Args:
        port: Gateway port to check
        project_dir: Project directory
        required_disk_gb: Required disk space in GB
        strict: Raise exception on failure

    Returns:
        True if all checks passed

    Raises:
        ValidationError if strict=True and checks fail
    """
    logger.info("Validating prerequisites...")

    checks = validate_all_prerequisites(port, project_dir, required_disk_gb)
    all_passed = True

    for check_name, success, message in checks:
        if success:
            logger.info(f"✓ {check_name}: {message}")
        else:
            logger.error(f"✗ {check_name}: {message}")
            all_passed = False

    if not all_passed and strict:
        raise ValidationError("Prerequisites validation failed. Fix the issues above and try again.")

    return all_passed
