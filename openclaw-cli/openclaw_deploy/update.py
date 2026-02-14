"""
Update command implementation.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import DeploymentConfig, load_config
from .validators import validate_and_report
from .docker_utils import (
    build_image, stop_services, start_services,
    wait_for_healthy, check_container_exists, DockerError
)
from .rollback import RollbackManager


logger = logging.getLogger(__name__)


def run_update(
    config_file: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    no_cache: bool = True,
    skip_health_check: bool = False,
    auto_rollback: bool = True
) -> bool:
    """
    Update existing deployment.

    This rebuilds the Docker image and restarts the services.

    Args:
        config_file: Path to configuration file
        project_dir: Project directory
        no_cache: Build without cache (default: True for updates)
        skip_health_check: Skip health check after update
        auto_rollback: Enable automatic rollback on failure

    Returns:
        True if update succeeded
    """
    if project_dir is None:
        project_dir = Path.cwd()

    config = load_config(
        config_file=config_file,
        env_file=project_dir / '.env',
        project_dir=project_dir
    )

    # Check if deployment exists
    if not check_container_exists(config.container_name):
        logger.error(f"Container '{config.container_name}' does not exist")
        logger.error("Run 'openclaw-deploy deploy' first to create a deployment")
        return False

    # Initialize rollback manager
    rollback = RollbackManager(config)
    if not auto_rollback:
        rollback.disable()

    logger.info("=" * 50)
    logger.info("OpenClaw Update")
    logger.info("=" * 50)
    logger.info("")

    try:
        # Step 1: Validate prerequisites
        logger.info("Step 1/4: Validating prerequisites")
        logger.info("-" * 50)

        validate_and_report(
            port=config.gateway_port,
            project_dir=config.project_dir,
            required_disk_gb=5.0,
            strict=True
        )
        logger.info("")

        # Step 2: Stop services
        logger.info("Step 2/4: Stopping current services")
        logger.info("-" * 50)

        stop_services(config, remove_volumes=False)
        rollback.add_action("Start services", start_services, config)
        logger.info("")

        # Step 3: Rebuild image
        logger.info("Step 3/4: Rebuilding Docker image")
        logger.info("-" * 50)

        logger.info("Building with --no-cache to get latest OpenClaw version...")
        build_image(config, no_cache=no_cache)
        logger.info("")

        # Step 4: Start services
        logger.info("Step 4/4: Starting updated services")
        logger.info("-" * 50)

        start_services(config)
        rollback.clear()  # Clear rollback if start succeeded
        logger.info("")

        # Health check
        if not skip_health_check:
            logger.info("Verifying deployment health...")
            logger.info("-" * 50)

            healthy = wait_for_healthy(
                container_name=config.container_name,
                timeout=120,
                interval=5
            )

            if not healthy:
                logger.error("")
                logger.error("Health check failed after update!")
                logger.error("Check logs for details:")
                logger.error(f"  docker compose logs -f {config.container_name}")
                logger.error("")

                if auto_rollback:
                    logger.warning("Rolling back to previous state...")
                    stop_services(config)
                    # Note: Previous image is already overwritten, can't rollback to it
                    logger.warning("Previous image was overwritten. You may need to redeploy.")
                    return False

                return False

            logger.info("")

        # Success
        logger.info("=" * 50)
        logger.info("✓ Update completed successfully!")
        logger.info("=" * 50)
        logger.info("")
        logger.info(f"Web UI: http://localhost:{config.gateway_port}")
        logger.info("")

        return True

    except (DockerError, Exception) as e:
        logger.error("")
        logger.error(f"Update failed: {e}")
        logger.error("")

        if auto_rollback:
            logger.warning("Attempting to restart previous services...")
            rollback.execute()

        return False

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("Update interrupted by user")
        logger.warning("")

        if auto_rollback:
            rollback.execute()

        return False
