"""
Rollback functionality for failed deployments.
"""

import logging
from typing import List, Callable, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .config import DeploymentConfig
from .docker_utils import (
    stop_services, remove_container, remove_image,
    remove_volume, DockerError
)


logger = logging.getLogger(__name__)


@dataclass
class RollbackAction:
    """Represents a rollback action."""
    name: str
    action: Callable
    args: Tuple = ()
    kwargs: dict = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class RollbackManager:
    """Manages rollback actions for deployment."""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.actions: List[RollbackAction] = []
        self.enabled = True

    def add_action(self, name: str, action: Callable, *args, **kwargs) -> None:
        """
        Add a rollback action.

        Args:
            name: Action description
            action: Callable to execute for rollback
            *args: Positional arguments for action
            **kwargs: Keyword arguments for action
        """
        rollback_action = RollbackAction(
            name=name,
            action=action,
            args=args,
            kwargs=kwargs
        )
        self.actions.append(rollback_action)
        logger.debug(f"Added rollback action: {name}")

    def disable(self) -> None:
        """Disable rollback (don't execute on failure)."""
        self.enabled = False
        logger.debug("Rollback disabled")

    def clear(self) -> None:
        """Clear all rollback actions."""
        self.actions.clear()
        logger.debug("Rollback actions cleared")

    def execute(self) -> bool:
        """
        Execute all rollback actions in reverse order.

        Returns:
            True if rollback succeeded
        """
        if not self.enabled:
            logger.info("Rollback is disabled, skipping")
            return True

        if not self.actions:
            logger.info("No rollback actions to execute")
            return True

        logger.warning("Executing rollback...")
        logger.info(f"Rolling back {len(self.actions)} action(s)")

        success = True

        # Execute in reverse order (LIFO)
        for action in reversed(self.actions):
            try:
                logger.info(f"Rolling back: {action.name}")
                action.action(*action.args, **action.kwargs)
            except Exception as e:
                logger.error(f"Rollback action failed: {action.name} - {e}")
                success = False

        if success:
            logger.info("✓ Rollback completed successfully")
        else:
            logger.warning("⚠ Rollback completed with some errors")

        return success


def cleanup_failed_deployment(config: DeploymentConfig, remove_volumes: bool = False) -> None:
    """
    Clean up a failed deployment.

    Args:
        config: Deployment configuration
        remove_volumes: Remove persistent volumes
    """
    logger.info("Cleaning up failed deployment...")

    # Stop services
    try:
        stop_services(config, remove_volumes=remove_volumes)
    except Exception as e:
        logger.warning(f"Error stopping services: {e}")

    # Remove container
    try:
        remove_container(config.container_name, force=True)
    except Exception as e:
        logger.warning(f"Error removing container: {e}")

    # Remove image (optional)
    # try:
    #     remove_image(config.image_name, force=True)
    # except Exception as e:
    #     logger.warning(f"Error removing image: {e}")

    # Remove volumes if requested
    if remove_volumes:
        try:
            remove_volume(config.home_volume, force=True)
        except Exception as e:
            logger.warning(f"Error removing volume: {e}")

    logger.info("✓ Cleanup completed")


def remove_env_file(env_file: Path) -> None:
    """Remove .env file."""
    try:
        if env_file.exists():
            env_file.unlink()
            logger.debug(f"Removed file: {env_file}")
    except Exception as e:
        logger.warning(f"Error removing env file: {e}")


def remove_directories(directories: List[Path]) -> None:
    """Remove directories."""
    import shutil

    for directory in directories:
        try:
            if directory.exists():
                shutil.rmtree(directory)
                logger.debug(f"Removed directory: {directory}")
        except Exception as e:
            logger.warning(f"Error removing directory {directory}: {e}")
