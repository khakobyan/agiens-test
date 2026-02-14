# Installation Guide

Complete installation guide for the OpenClaw Deploy CLI tool.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Post-Installation](#post-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.8 or higher
- **Docker**: 24.0 or higher
- **Docker Compose**: V2 (included with Docker Desktop)
- **Disk Space**: Minimum 5 GB free space
- **Memory**: Minimum 4 GB RAM (8 GB recommended)

### Check Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check Docker version
docker --version   # Should be 24.0+

# Check Docker Compose
docker compose version  # Should be v2.x

# Check Docker is running
docker info

# Check disk space
df -h
```

## Installation Methods

### Method 1: Install from Source (Recommended for Development)

```bash
# Clone the repository (or navigate to the openclaw-cli directory)
cd openclaw-cli

# Install in development mode (editable install)
pip install -e .

# Or install in production mode
pip install .
```

**Benefits:**
- Easy to modify and test changes
- Immediate access to updates
- Full access to source code

### Method 2: Install from PyPI (When Published)

```bash
# Install latest stable version
pip install openclaw-deploy

# Install specific version
pip install openclaw-deploy==1.0.0

# Upgrade to latest version
pip install --upgrade openclaw-deploy
```

### Method 3: Install with pipx (Isolated Environment)

[pipx](https://pypa.github.io/pipx/) installs CLI tools in isolated environments:

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install openclaw-deploy with pipx
pipx install openclaw-deploy

# Or from source
pipx install /path/to/openclaw-cli
```

**Benefits:**
- Isolated environment (no conflicts with other packages)
- Easy to uninstall cleanly
- Recommended for end-users

### Method 4: Install in Virtual Environment

```bash
# Create virtual environment
python3 -m venv openclaw-env

# Activate virtual environment
source openclaw-env/bin/activate  # Linux/macOS
# or
openclaw-env\Scripts\activate     # Windows

# Install the tool
pip install /path/to/openclaw-cli

# Tool is now available while venv is activated
openclaw-deploy --version
```

**Benefits:**
- Isolated from system Python packages
- Clean uninstallation
- Good for testing

## Post-Installation

### 1. Verify Installation

```bash
# Check that openclaw-deploy is available
which openclaw-deploy

# Check version
openclaw-deploy --version

# View help
openclaw-deploy --help
```

### 2. Prepare Deployment Directory

```bash
# Navigate to your OpenClaw deployment directory
# (the directory containing Dockerfile, docker-compose.yml, etc.)
cd /path/to/openclaw-deployment

# Verify required files exist
ls -la Dockerfile docker-compose.yml .env.example
```

### 3. Configure API Keys (Optional)

You can configure API keys before deployment:

```bash
# Option A: Use deploy command with --api-key flag
openclaw-deploy deploy --api-key sk-ant-your-key

# Option B: Create .env file manually
cp .env.example .env
vim .env  # Add your API keys
```

### 4. Set Up Docker Permissions (Linux)

On Linux, ensure your user can run Docker without sudo:

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Test Docker access
docker ps
```

## Verification

### Quick Verification

```bash
# Run a simple status check
openclaw-deploy status

# This should show that no deployment exists yet
```

### Full Verification

```bash
# Run a test deployment
openclaw-deploy deploy --no-interactive --skip-health-check

# Check status
openclaw-deploy status

# Clean up
openclaw-deploy cleanup --no-interactive
```

### Test Suite Verification

If you installed from source:

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run tests
cd openclaw-cli
pytest

# Run with coverage
pytest --cov=openclaw_deploy
```

## Troubleshooting

### Issue: Command Not Found

```bash
# If 'openclaw-deploy' is not found after installation:

# 1. Check if it's installed
pip list | grep openclaw-deploy

# 2. Check Python scripts directory is in PATH
python3 -m site --user-base
# Add <user-base>/bin to your PATH

# 3. Add to PATH in ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

### Issue: Permission Denied

```bash
# If you get permission errors during installation:

# Option 1: Install for current user only
pip install --user /path/to/openclaw-cli

# Option 2: Use sudo (not recommended)
sudo pip install /path/to/openclaw-cli

# Option 3: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install /path/to/openclaw-cli
```

### Issue: Docker Connection Error

```bash
# If deployment fails with Docker connection error:

# 1. Verify Docker is running
systemctl status docker  # Linux
# or
docker info

# 2. Start Docker if stopped
sudo systemctl start docker  # Linux
# or open Docker Desktop

# 3. Check Docker permissions
docker ps
# If this fails, add user to docker group (see above)
```

### Issue: Python Version Mismatch

```bash
# If Python version is < 3.8:

# 1. Check available Python versions
python3 --version
python3.8 --version
python3.9 --version

# 2. Install using specific Python version
python3.9 -m pip install /path/to/openclaw-cli

# 3. Or use pyenv to install newer Python
# See: https://github.com/pyenv/pyenv
```

### Issue: Dependency Conflicts

```bash
# If you encounter package dependency conflicts:

# 1. Use pipx (isolated environment)
pipx install /path/to/openclaw-cli

# 2. Or create fresh virtual environment
python3 -m venv fresh-env
source fresh-env/bin/activate
pip install /path/to/openclaw-cli
```

## Configuration

### Shell Completion (Optional)

Enable shell completion for better CLI experience:

#### Bash

```bash
# Add to ~/.bashrc
eval "$(_OPENCLAW_DEPLOY_COMPLETE=bash_source openclaw-deploy)"

# Reload shell
source ~/.bashrc
```

#### Zsh

```bash
# Add to ~/.zshrc
eval "$(_OPENCLAW_DEPLOY_COMPLETE=zsh_source openclaw-deploy)"

# Reload shell
source ~/.zshrc
```

#### Fish

```fish
# Add to ~/.config/fish/config.fish
eval (env _OPENCLAW_DEPLOY_COMPLETE=fish_source openclaw-deploy)
```

## Upgrading

### Upgrade from PyPI

```bash
# Upgrade to latest version
pip install --upgrade openclaw-deploy

# Or with pipx
pipx upgrade openclaw-deploy
```

### Upgrade from Source

```bash
# Pull latest changes
cd openclaw-cli
git pull

# Reinstall
pip install --upgrade .
```

## Uninstallation

### Uninstall the Tool

```bash
# With pip
pip uninstall openclaw-deploy

# With pipx
pipx uninstall openclaw-deploy
```

### Clean Up Data

```bash
# Remove OpenClaw data directories (optional)
rm -rf ~/.openclaw
rm -rf ~/openclaw

# Remove Docker volumes (optional)
docker volume rm openclaw-home

# Remove logs (optional)
rm -rf ~/.openclaw/logs
```

### Complete Cleanup

```bash
# Remove everything
openclaw-deploy cleanup --all --no-interactive
pip uninstall openclaw-deploy
rm -rf ~/.openclaw ~/openclaw
docker volume rm openclaw-home
```

## Next Steps

After installation:

1. **Read the README**: `openclaw-cli/README.md`
2. **Review Configuration**: `openclaw-cli/config/example.yaml`
3. **Deploy OpenClaw**: `openclaw-deploy deploy`
4. **Check Status**: `openclaw-deploy status`
5. **View Logs**: `openclaw-deploy logs --follow`

## Getting Help

- **Built-in Help**: `openclaw-deploy --help`
- **Command Help**: `openclaw-deploy deploy --help`
- **Documentation**: See `README.md` and `docs/` directory
- **Issues**: Report at GitHub Issues

## Platform-Specific Notes

### Linux

- Ensure Docker daemon is running: `systemctl status docker`
- Add user to docker group to avoid using sudo
- Default installation: `~/.local/bin/openclaw-deploy`

### macOS

- Install Docker Desktop for Mac
- Docker socket typically at `/var/run/docker.sock`
- May need to adjust Docker Desktop resource limits

### Windows (WSL2)

- Requires WSL2 and Docker Desktop for Windows
- Run all commands in WSL2 terminal
- Ensure Docker Desktop WSL2 backend is enabled
- File paths should use WSL format: `/home/user/...`

## Advanced Installation

### Install with Extra Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install with documentation dependencies
pip install -e ".[docs]"

# Install with all extras
pip install -e ".[all]"
```

### Custom Installation Location

```bash
# Install to custom prefix
pip install --prefix=/opt/openclaw /path/to/openclaw-cli

# Add to PATH
export PATH="/opt/openclaw/bin:$PATH"
```

### Docker-only Installation

If you prefer not to install Python packages:

```bash
# Run directly with Python module
python3 -m openclaw_deploy.cli --help

# Or create an alias
alias openclaw-deploy='python3 -m openclaw_deploy.cli'
```
