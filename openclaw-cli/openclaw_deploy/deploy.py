"""
Deployment command implementation.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from .config import DeploymentConfig, load_config
from .validators import validate_and_report, ValidationError
from .docker_utils import (
    create_directories, generate_env_file, build_image,
    start_services, wait_for_healthy, get_logs, DockerError
)
from .rollback import RollbackManager, cleanup_failed_deployment


logger = logging.getLogger(__name__)


def run_deploy(
    config_file: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    gateway_token: Optional[str] = None,
    api_key: Optional[str] = None,
    no_cache: bool = False,
    skip_health_check: bool = False,
    interactive: bool = True,
    auto_rollback: bool = True
) -> bool:
    """
    Execute full deployment workflow.

    Args:
        config_file: Path to configuration file
        project_dir: Project directory (default: current directory)
        gateway_token: Gateway authentication token
        api_key: API key (Anthropic, OpenAI, etc.)
        no_cache: Build without cache
        skip_health_check: Skip health check after deployment
        interactive: Enable interactive prompts
        auto_rollback: Enable automatic rollback on failure

    Returns:
        True if deployment succeeded

    Raises:
        ValidationError: If prerequisites check fails
        DockerError: If Docker operations fail
    """
    # Load configuration
    if project_dir is None:
        project_dir = Path.cwd()

    config = load_config(
        config_file=config_file,
        env_file=project_dir / '.env',
        project_dir=project_dir,
        gateway_token=gateway_token
    )

    # Set API key if provided
    if api_key:
        if not config.anthropic_api_key:
            config.anthropic_api_key = api_key

    # Initialize rollback manager
    rollback = RollbackManager(config)
    if not auto_rollback:
        rollback.disable()

    logger.info("=" * 50)
    logger.info("OpenClaw Deployment")
    logger.info("=" * 50)
    logger.info("")

    try:
        # Step 1: Validate prerequisites
        logger.info("Step 1/6: Validating prerequisites")
        logger.info("-" * 50)

        validate_and_report(
            port=config.gateway_port,
            project_dir=config.project_dir,
            required_disk_gb=5.0,
            strict=True
        )
        logger.info("")

        # Step 2: Create directories
        logger.info("Step 2/6: Creating host directories")
        logger.info("-" * 50)

        create_directories(config)
        # No rollback needed for directory creation (harmless to keep)
        logger.info("")

        # Step 3: Generate environment file
        logger.info("Step 3/6: Generating environment configuration")
        logger.info("-" * 50)

        env_file = config.project_dir / '.env'
        if env_file.exists() and interactive:
            logger.warning(f".env file already exists: {env_file}")
            response = input("Overwrite existing .env file? [y/N]: ").strip().lower()
            if response != 'y':
                logger.info("Keeping existing .env file")
            else:
                generate_env_file(config)
                rollback.add_action("Remove .env file", env_file.unlink)
        else:
            generate_env_file(config)
            rollback.add_action("Remove .env file", env_file.unlink)

        # Warn if no API keys configured
        if not any([config.anthropic_api_key, config.openai_api_key,
                   config.google_ai_api_key, config.ollama_base_url]):
            logger.warning("")
            logger.warning("⚠ No API keys configured!")
            logger.warning(f"Edit {env_file} to add your API keys before the gateway will work.")
            logger.warning("")

        logger.info("")

        # Step 4: Build Docker image
        logger.info("Step 4/6: Building Docker image")
        logger.info("-" * 50)

        build_image(config, no_cache=no_cache)
        # Rollback: remove image (commented out to keep useful build artifacts)
        # rollback.add_action("Remove image", remove_image, config.image_name, True)
        logger.info("")

        # Step 5: Start services
        logger.info("Step 5/6: Starting services")
        logger.info("-" * 50)

        start_services(config)
        rollback.add_action("Stop services", cleanup_failed_deployment, config, False)
        logger.info("")

        # Step 6: Health check
        if not skip_health_check:
            logger.info("Step 6/6: Verifying deployment health")
            logger.info("-" * 50)

            healthy = wait_for_healthy(
                container_name=config.container_name,
                timeout=120,
                interval=5
            )

            if not healthy:
                logger.error("")
                logger.error("Health check failed!")
                logger.error("Check logs for details:")
                logger.error(f"  docker compose logs -f {config.container_name}")
                logger.error("")

                if auto_rollback:
                    rollback.execute()
                    return False
                else:
                    logger.warning("Auto-rollback is disabled. Services are still running.")
                    logger.warning("Run 'openclaw-deploy cleanup' to remove the deployment.")
                    return False

            logger.info("")
        else:
            logger.info("Step 6/6: Health check skipped")
            logger.info("")

        # Success - clear rollback actions
        rollback.clear()

        # Print access information
        logger.info("=" * 50)
        logger.info("✓ Deployment completed successfully!")
        logger.info("=" * 50)
        logger.info("")
        logger.info(f"Web UI:  http://localhost:{config.gateway_port}")

        if config.gateway_token:
            logger.info(f"Token:   {config.gateway_token}")
            logger.info("")
            logger.info("Full URL:")
            logger.info(f"  http://localhost:{config.gateway_port}?token={config.gateway_token}")

        logger.info("")
        logger.info("Useful commands:")
        logger.info("  openclaw-deploy status      # Check deployment status")
        logger.info("  openclaw-deploy cleanup     # Remove deployment")
        logger.info("  docker compose logs -f      # View logs")
        logger.info("")

        return True

    except (ValidationError, DockerError) as e:
        logger.error("")
        logger.error(f"Deployment failed: {e}")
        logger.error("")

        if auto_rollback:
            rollback.execute()

        return False

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("Deployment interrupted by user")
        logger.warning("")

        if auto_rollback:
            rollback.execute()

        return False

    except Exception as e:
        logger.error("")
        logger.error(f"Unexpected error during deployment: {e}")
        logger.error("")

        if auto_rollback:
            rollback.execute()

        return False
