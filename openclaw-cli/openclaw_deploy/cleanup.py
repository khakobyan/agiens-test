"""
Cleanup command implementation.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import DeploymentConfig, load_config
from .docker_utils import (
    stop_services, remove_container, remove_image,
    remove_volume, check_container_exists
)


logger = logging.getLogger(__name__)


def run_cleanup(
    config_file: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    remove_volumes: bool = False,
    remove_image: bool = False,
    remove_config: bool = False,
    interactive: bool = True
) -> bool:
    """
    Clean up deployment.

    Args:
        config_file: Path to configuration file
        project_dir: Project directory
        remove_volumes: Remove persistent volumes
        remove_image: Remove Docker image
        remove_config: Remove .env configuration file
        interactive: Prompt for confirmation

    Returns:
        True if cleanup succeeded
    """
    if project_dir is None:
        project_dir = Path.cwd()

    config = load_config(
        config_file=config_file,
        env_file=project_dir / '.env',
        project_dir=project_dir
    )

    logger.info("=" * 50)
    logger.info("OpenClaw Cleanup")
    logger.info("=" * 50)
    logger.info("")

    # Check if deployment exists
    if not check_container_exists(config.container_name):
        logger.warning(f"Container '{config.container_name}' does not exist")
        logger.info("Nothing to clean up")
        return True

    # Interactive confirmation
    if interactive:
        logger.warning("This will remove the OpenClaw deployment:")
        logger.warning(f"  - Container: {config.container_name}")

        if remove_volumes:
            logger.warning(f"  - Volume: {config.home_volume}")
            logger.warning(f"  - Data: {config.openclaw_home}")

        if remove_image:
            logger.warning(f"  - Image: {config.image_name}")

        if remove_config:
            logger.warning(f"  - Config: {config.project_dir / '.env'}")

        logger.warning("")
        response = input("Continue with cleanup? [y/N]: ").strip().lower()

        if response != 'y':
            logger.info("Cleanup cancelled")
            return False

        logger.info("")

    try:
        # Stop services
        logger.info("Stopping services...")
        stop_services(config, remove_volumes=remove_volumes)

        # Remove container
        logger.info(f"Removing container: {config.container_name}")
        from .docker_utils import remove_container as remove_container_fn
        remove_container_fn(config.container_name, force=True)

        # Remove volumes
        if remove_volumes:
            logger.info(f"Removing volume: {config.home_volume}")
            remove_volume(config.home_volume, force=True)

            # Optionally remove host directories
            logger.warning("")
            logger.warning(f"Host directories still exist:")
            logger.warning(f"  - {config.openclaw_home}")
            logger.warning(f"  - {config.workspace_dir}")
            logger.warning("")
            logger.warning("To remove them manually, run:")
            logger.warning(f"  rm -rf {config.openclaw_home}")
            logger.warning(f"  rm -rf {config.workspace_dir}")
            logger.warning("")

        # Remove image
        if remove_image:
            logger.info(f"Removing image: {config.image_name}")
            from .docker_utils import remove_image as remove_image_fn
            remove_image_fn(config.image_name, force=True)

        # Remove config file
        if remove_config:
            env_file = config.project_dir / '.env'
            if env_file.exists():
                logger.info(f"Removing config: {env_file}")
                env_file.unlink()

        logger.info("")
        logger.info("=" * 50)
        logger.info("✓ Cleanup completed successfully")
        logger.info("=" * 50)
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False
