# OpenClaw Deploy - Automation CLI Tool

A production-ready CLI tool for automating [OpenClaw](https://github.com/openclaw/openclaw) Docker deployments with intelligent rollback, health verification, and comprehensive error handling.

## Features

- **Automated Deployment**: Full deployment workflow with prerequisite validation
- **Intelligent Rollback**: Automatic rollback on deployment failures
- **Health Verification**: Built-in health checks with customizable timeouts
- **Idempotent Operations**: Safe to run multiple times
- **Interactive & Non-Interactive Modes**: Supports both manual and automated workflows
- **Comprehensive Logging**: Detailed logs with color-coded output
- **Configuration Management**: Support for YAML config files and .env files
- **Progress Tracking**: Real-time progress indicators
- **Production-Ready**: Error handling, validation, and safety checks

## Quick Start

### Installation

```bash
# Install from source
cd openclaw-cli
pip install -e .

# Or install with pip (when published)
pip install openclaw-deploy
```

### Basic Usage

```bash
# Deploy OpenClaw (interactive mode)
openclaw-deploy deploy

# Check deployment status
openclaw-deploy status

# View logs
openclaw-deploy logs --follow

# Update to latest version
openclaw-deploy update

# Clean up deployment
openclaw-deploy cleanup
```

## Commands

### `deploy` - Full Deployment

Deploy OpenClaw Docker environment with full automation:

```bash
# Interactive deployment (prompts for confirmations)
openclaw-deploy deploy

# Non-interactive deployment with API key
openclaw-deploy deploy --api-key sk-ant-your-key --no-interactive

# Deploy with custom token
openclaw-deploy deploy --gateway-token my-secure-token

# Deploy without cache (force rebuild)
openclaw-deploy deploy --no-cache

# Deploy without health check
openclaw-deploy deploy --skip-health-check

# Deploy without automatic rollback on failure
openclaw-deploy deploy --no-rollback
```

**Deployment Steps:**
1. Validates prerequisites (Docker, permissions, disk space)
2. Creates required host directories
3. Generates environment configuration
4. Builds Docker image
5. Starts services
6. Verifies deployment health

On failure, automatically rolls back changes unless `--no-rollback` is specified.

### `status` - Check Status

Check deployment status and health:

```bash
# Basic status check
openclaw-deploy status

# Verbose status with configuration details
openclaw-deploy status --verbose
```

Shows:
- Container existence and running state
- Health check status
- Access URLs
- Configuration summary (with `--verbose`)
- API key configuration status

### `cleanup` - Remove Deployment

Remove OpenClaw deployment:

```bash
# Remove container only (preserve data)
openclaw-deploy cleanup

# Remove container and volumes
openclaw-deploy cleanup --volumes

# Remove container and image
openclaw-deploy cleanup --image

# Remove container and configuration
openclaw-deploy cleanup --config

# Remove everything
openclaw-deploy cleanup --all

# Non-interactive cleanup (skip confirmation)
openclaw-deploy cleanup --all --no-interactive
```

### `update` - Update Deployment

Update existing deployment to latest OpenClaw version:

```bash
# Standard update (rebuilds without cache)
openclaw-deploy update

# Update with cache (faster but may not get latest)
openclaw-deploy update --no-cache=false

# Update without health check
openclaw-deploy update --skip-health-check
```

**Update Process:**
1. Validates prerequisites
2. Stops current services
3. Rebuilds Docker image (pulls latest OpenClaw)
4. Starts updated services
5. Verifies deployment health

### `logs` - View Logs

View deployment logs:

```bash
# Show last 50 lines
openclaw-deploy logs

# Show last 100 lines
openclaw-deploy logs --tail 100

# Follow logs (live stream)
openclaw-deploy logs --follow
```

## Configuration

### Configuration Files

The tool supports two configuration methods:

1. **YAML Configuration** (`config.yaml`)
2. **Environment File** (`.env`)

#### YAML Configuration

```yaml
# config.yaml
project_dir: "/path/to/deployment"
gateway_token: "your-secure-token"
gateway_port: 18789
anthropic_api_key: "sk-ant-your-key"
```

Use with:
```bash
openclaw-deploy --config config.yaml deploy
```

#### Environment File

The tool reads `.env` from the project directory:

```bash
# .env
OPENCLAW_GATEWAY_TOKEN=your-secure-token
ANTHROPIC_API_KEY=sk-ant-your-key
OPENCLAW_GATEWAY_BIND=lan
```

### Configuration Options

| Option | Environment Variable | Description | Default |
|--------|---------------------|-------------|---------|
| `gateway_token` | `OPENCLAW_GATEWAY_TOKEN` | Auth token for web UI | Auto-generated |
| `gateway_bind` | `OPENCLAW_GATEWAY_BIND` | Network bind mode | `lan` |
| `gateway_port` | - | Gateway port | `18789` |
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `openai_api_key` | `OPENAI_API_KEY` | OpenAI API key | - |
| `google_ai_api_key` | `GOOGLE_AI_API_KEY` | Google AI API key | - |
| `ollama_base_url` | `OLLAMA_BASE_URL` | Ollama server URL | - |
| `apt_packages` | `OPENCLAW_DOCKER_APT_PACKAGES` | Extra system packages | - |
| `home_volume` | `OPENCLAW_HOME_VOLUME` | Named volume for /home/node | `openclaw-home` |

See `config/example.yaml` for a complete configuration template.

## Global Options

```bash
# Enable verbose logging
openclaw-deploy --verbose deploy

# Use custom project directory
openclaw-deploy --project-dir /path/to/project deploy

# Use custom config file
openclaw-deploy --config myconfig.yaml deploy

# Use custom log file
openclaw-deploy --log-file /path/to/deploy.log deploy
```

## Prerequisites

The tool automatically validates these prerequisites:

- **Docker** 24+ with daemon running
- **Docker Compose** V2
- **Available port** (default: 18789)
- **Disk space** (minimum 5 GB)
- **Docker permissions** (user in docker group or sudo)
- **Required files** (Dockerfile, docker-compose.yml, .env.example)

## Advanced Usage

### Automated Deployment in CI/CD

```bash
# Non-interactive deployment with all parameters
openclaw-deploy --verbose \
  deploy \
  --api-key "$ANTHROPIC_API_KEY" \
  --gateway-token "$GATEWAY_TOKEN" \
  --no-interactive \
  --no-cache
```

### Configuration File Workflow

```bash
# 1. Create config from example
cp config/example.yaml my-deployment.yaml

# 2. Edit configuration
vim my-deployment.yaml

# 3. Deploy with config
openclaw-deploy --config my-deployment.yaml deploy
```

### Health Check Customization

Edit the deployment configuration to customize health check parameters:

```yaml
health_interval: 30      # Check every 30 seconds
health_timeout: 10       # Timeout after 10 seconds
health_start_period: 60  # Wait 60s before first check
health_retries: 3        # Retry 3 times before marking unhealthy
```

## Troubleshooting

### Deployment Fails with Permission Error

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo openclaw-deploy deploy
```

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :18789

# Or use a different port in config
gateway_port: 8080
```

### Health Check Fails

```bash
# View logs to diagnose
openclaw-deploy logs --tail 100

# Or check directly
docker compose logs openclaw-gateway
```

### Rollback Failed

If automatic rollback fails, manually clean up:

```bash
# Stop and remove everything
openclaw-deploy cleanup --all --no-interactive

# Then try deployment again
openclaw-deploy deploy
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=openclaw_deploy --cov-report=html

# Run specific test
pytest tests/test_validators.py
```

### Project Structure

```
openclaw-cli/
├── openclaw_deploy/       # Main package
│   ├── cli.py            # CLI entry point
│   ├── deploy.py         # Deploy command
│   ├── status.py         # Status command
│   ├── cleanup.py        # Cleanup command
│   ├── update.py         # Update command
│   ├── config.py         # Configuration management
│   ├── validators.py     # Prerequisite validation
│   ├── docker_utils.py   # Docker operations
│   ├── rollback.py       # Rollback functionality
│   └── logger.py         # Logging setup
├── tests/                # Unit tests
├── config/               # Example configurations
├── docs/                 # Additional documentation
└── setup.py             # Package setup
```

## Architecture

### Deployment Flow

```
User Command
    ↓
CLI Parser (Click)
    ↓
Command Handler (deploy.py, status.py, etc.)
    ↓
├─→ Validators (prerequisites check)
├─→ Config Manager (load configuration)
├─→ Docker Utils (Docker operations)
└─→ Rollback Manager (error recovery)
    ↓
Success / Failure
```

### Rollback Mechanism

The tool maintains a stack of rollback actions during deployment:

1. Each successful operation adds a rollback action
2. On failure, rollback actions execute in reverse order (LIFO)
3. Rollback can be disabled with `--no-rollback`

Example:
```
Operation         Rollback Action
---------         ---------------
Create .env    →  Remove .env
Build image    →  (Keep image - useful for debugging)
Start services →  Stop services & remove containers
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Related Projects

- [OpenClaw](https://github.com/openclaw/openclaw) - The open-source personal AI agent
- [Docker](https://www.docker.com/) - Container platform

## Support

- **Issues**: [GitHub Issues](https://github.com/openclaw/openclaw-deploy/issues)
- **Documentation**: [GitHub Wiki](https://github.com/openclaw/openclaw-deploy/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/openclaw/openclaw-deploy/discussions)
