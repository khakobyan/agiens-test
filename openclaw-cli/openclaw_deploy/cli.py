"""
Main CLI entry point for OpenClaw deployment tool.
"""

import sys
import click
from pathlib import Path
from typing import Optional

from . import __version__
from .logger import setup_logger, get_default_log_file
from .deploy import run_deploy
from .status import run_status
from .cleanup import run_cleanup
from .update import run_update


# Global options
class GlobalOptions:
    """Store global CLI options."""
    def __init__(self):
        self.verbose = False
        self.log_file = None
        self.project_dir = None
        self.config_file = None


pass_global = click.make_pass_decorator(GlobalOptions, ensure=True)


@click.group()
@click.version_option(version=__version__, prog_name='openclaw-deploy')
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--log-file',
    type=click.Path(dir_okay=False, path_type=Path),
    help='Log file path (default: ~/.openclaw/logs/deploy_<timestamp>.log)'
)
@click.option(
    '--project-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Project directory (default: current directory)'
)
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help='Configuration file (YAML)'
)
@click.pass_context
def cli(ctx, verbose, log_file, project_dir, config):
    """
    OpenClaw Deployment Automation Tool

    A production-ready CLI tool for automating OpenClaw Docker deployments.
    """
    # Store global options
    ctx.obj = GlobalOptions()
    ctx.obj.verbose = verbose
    ctx.obj.log_file = log_file or get_default_log_file()
    ctx.obj.project_dir = project_dir or Path.cwd()
    ctx.obj.config_file = config

    # Setup logging
    setup_logger(
        name='openclaw_deploy',
        verbose=verbose,
        log_file=ctx.obj.log_file
    )


@cli.command()
@click.option(
    '--gateway-token',
    help='Gateway authentication token (auto-generated if not provided)'
)
@click.option(
    '--api-key',
    help='API key for model provider (Anthropic, OpenAI, etc.)'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Build Docker image without cache'
)
@click.option(
    '--skip-health-check',
    is_flag=True,
    help='Skip health check after deployment'
)
@click.option(
    '--no-interactive',
    is_flag=True,
    help='Disable interactive prompts'
)
@click.option(
    '--no-rollback',
    is_flag=True,
    help='Disable automatic rollback on failure'
)
@pass_global
def deploy(global_opts, gateway_token, api_key, no_cache, skip_health_check, no_interactive, no_rollback):
    """
    Deploy OpenClaw Docker environment.

    This command performs a full deployment workflow:
    1. Validates prerequisites (Docker, permissions, disk space)
    2. Creates required host directories
    3. Generates environment configuration
    4. Builds Docker image
    5. Starts services
    6. Verifies deployment health

    If deployment fails, it will automatically rollback changes unless --no-rollback is specified.
    """
    success = run_deploy(
        config_file=global_opts.config_file,
        project_dir=global_opts.project_dir,
        gateway_token=gateway_token,
        api_key=api_key,
        no_cache=no_cache,
        skip_health_check=skip_health_check,
        interactive=not no_interactive,
        auto_rollback=not no_rollback
    )

    sys.exit(0 if success else 1)


@cli.command()
@pass_global
def status(global_opts):
    """
    Check deployment status.

    Shows the current state of the OpenClaw deployment including:
    - Container status (running/stopped)
    - Health check status
    - Access URLs
    - Configuration summary (with --verbose)
    """
    success = run_status(
        config_file=global_opts.config_file,
        project_dir=global_opts.project_dir,
        verbose=global_opts.verbose
    )

    sys.exit(0 if success else 1)


@cli.command()
@click.option(
    '--volumes',
    is_flag=True,
    help='Remove persistent volumes'
)
@click.option(
    '--image',
    is_flag=True,
    help='Remove Docker image'
)
@click.option(
    '--config',
    'remove_config',
    is_flag=True,
    help='Remove .env configuration file'
)
@click.option(
    '--all',
    'remove_all',
    is_flag=True,
    help='Remove everything (volumes, image, config)'
)
@click.option(
    '--no-interactive',
    is_flag=True,
    help='Skip confirmation prompt'
)
@pass_global
def cleanup(global_opts, volumes, image, remove_config, remove_all, no_interactive):
    """
    Clean up OpenClaw deployment.

    By default, this removes the container while preserving volumes and data.
    Use flags to remove additional components:
    - --volumes: Remove persistent volumes and data
    - --image: Remove Docker image
    - --config: Remove .env configuration file
    - --all: Remove everything

    This operation requires confirmation unless --no-interactive is specified.
    """
    if remove_all:
        volumes = True
        image = True
        remove_config = True

    success = run_cleanup(
        config_file=global_opts.config_file,
        project_dir=global_opts.project_dir,
        remove_volumes=volumes,
        remove_image=image,
        remove_config=remove_config,
        interactive=not no_interactive
    )

    sys.exit(0 if success else 1)


@cli.command()
@click.option(
    '--no-cache',
    is_flag=True,
    default=True,
    help='Build without cache (default: enabled)'
)
@click.option(
    '--skip-health-check',
    is_flag=True,
    help='Skip health check after update'
)
@click.option(
    '--no-rollback',
    is_flag=True,
    help='Disable automatic rollback on failure'
)
@pass_global
def update(global_opts, no_cache, skip_health_check, no_rollback):
    """
    Update existing OpenClaw deployment.

    This rebuilds the Docker image (pulling latest OpenClaw version)
    and restarts the services with the new image.

    The update process:
    1. Validates prerequisites
    2. Stops current services
    3. Rebuilds Docker image (with --no-cache by default)
    4. Starts updated services
    5. Verifies deployment health

    If update fails, it will attempt to restart the previous services.
    Note: The previous image is overwritten, so full rollback is not possible.
    """
    success = run_update(
        config_file=global_opts.config_file,
        project_dir=global_opts.project_dir,
        no_cache=no_cache,
        skip_health_check=skip_health_check,
        auto_rollback=not no_rollback
    )

    sys.exit(0 if success else 1)


@cli.command()
@click.option(
    '--tail',
    default=50,
    type=int,
    help='Number of log lines to show (default: 50)'
)
@click.option(
    '--follow',
    '-f',
    is_flag=True,
    help='Follow log output'
)
@pass_global
def logs(global_opts, tail, follow):
    """
    View deployment logs.

    Shows logs from the OpenClaw gateway container.
    Use --follow to continuously stream logs.
    """
    from .docker_utils import get_logs
    from .config import load_config

    config = load_config(
        config_file=global_opts.config_file,
        env_file=global_opts.project_dir / '.env',
        project_dir=global_opts.project_dir
    )

    get_logs(config, tail=tail, follow=follow)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
