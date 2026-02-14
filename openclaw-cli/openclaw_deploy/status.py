"""
Status command implementation.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import DeploymentConfig, load_config
from .docker_utils import get_deployment_info, get_container_status, get_container_health


logger = logging.getLogger(__name__)


def run_status(
    config_file: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    verbose: bool = False
) -> bool:
    """
    Check deployment status.

    Args:
        config_file: Path to configuration file
        project_dir: Project directory
        verbose: Show detailed information

    Returns:
        True if deployment is healthy
    """
    if project_dir is None:
        project_dir = Path.cwd()

    config = load_config(
        config_file=config_file,
        env_file=project_dir / '.env',
        project_dir=project_dir
    )

    logger.info("=" * 50)
    logger.info("OpenClaw Deployment Status")
    logger.info("=" * 50)
    logger.info("")

    # Get deployment info
    info = get_deployment_info(config)

    # Container status
    logger.info(f"Container Name:    {config.container_name}")
    logger.info(f"Container Exists:  {'✓ Yes' if info['container_exists'] else '✗ No'}")

    if info['container_exists']:
        status = info['container_status']
        running = info['container_running']
        health = info['container_health']

        logger.info(f"Container Running: {'✓ Yes' if running else '✗ No'}")
        logger.info(f"Container Status:  {status}")

        if health:
            if health == 'healthy':
                logger.info(f"Health Check:      ✓ {health.upper()}")
            elif health == 'unhealthy':
                logger.error(f"Health Check:      ✗ {health.upper()}")
            else:
                logger.warning(f"Health Check:      {health}")
        else:
            logger.info(f"Health Check:      N/A")

        logger.info("")
        logger.info(f"Gateway URL:       {info['gateway_url']}")

        if 'gateway_url_with_token' in info:
            logger.info(f"Access URL:        {info['gateway_url_with_token']}")

        # Show additional info if verbose
        if verbose:
            logger.info("")
            logger.info("Configuration:")
            logger.info(f"  Project Dir:     {config.project_dir}")
            logger.info(f"  OpenClaw Home:   {config.openclaw_home}")
            logger.info(f"  Workspace:       {config.workspace_dir}")
            logger.info(f"  Image:           {config.image_name}")
            logger.info(f"  Gateway Port:    {config.gateway_port}")
            logger.info(f"  Gateway Bind:    {config.gateway_bind}")

            # Check API keys (without revealing them)
            logger.info("")
            logger.info("API Keys Configured:")
            logger.info(f"  Anthropic:       {'✓ Yes' if config.anthropic_api_key else '✗ No'}")
            logger.info(f"  OpenAI:          {'✓ Yes' if config.openai_api_key else '✗ No'}")
            logger.info(f"  Google AI:       {'✓ Yes' if config.google_ai_api_key else '✗ No'}")
            logger.info(f"  Ollama URL:      {'✓ Yes' if config.ollama_base_url else '✗ No'}")

    else:
        logger.warning("Container does not exist. Run 'openclaw-deploy deploy' to create it.")

    logger.info("")

    # Determine overall health
    is_healthy = (
        info['container_exists'] and
        info['container_running'] and
        (info['container_health'] == 'healthy' or info['container_health'] is None)
    )

    if is_healthy:
        logger.info("Status: ✓ HEALTHY")
    else:
        logger.warning("Status: ⚠ NOT HEALTHY")

    logger.info("")

    return is_healthy
