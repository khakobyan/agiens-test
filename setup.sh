#!/bin/bash
set -e

# OpenClaw Deployment - One-Command Setup Script
# This script checks prerequisites, installs the deployment tool, and runs the deployment

echo "=========================================="
echo "OpenClaw Deployment Setup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_info() {
    echo "ℹ $1"
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended"
    print_info "Consider running as a regular user in the docker group"
fi

# Step 1: Check Prerequisites
echo "Step 1: Checking prerequisites..."
echo "------------------------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker found (version $DOCKER_VERSION)"
else
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker daemon
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running or you don't have permission"
    echo "Try: sudo systemctl start docker"
    echo "Or add your user to the docker group: sudo usermod -aG docker \$USER"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | cut -d' ' -f4)
    print_success "Docker Compose found (version $COMPOSE_VERSION)"
else
    print_error "Docker Compose V2 is not installed"
    echo "Please install Docker Compose V2"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python found (version $PYTHON_VERSION)"
else
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    print_success "pip found"
else
    print_error "pip is not installed"
    echo "Please install pip: python3 -m ensurepip --upgrade"
    exit 1
fi

# Check disk space (require at least 5GB free)
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -ge 5 ]; then
    print_success "Sufficient disk space available (${AVAILABLE_SPACE}GB free)"
else
    print_warning "Low disk space: ${AVAILABLE_SPACE}GB free (5GB+ recommended)"
fi

echo ""

# Step 2: Install openclaw-deploy tool
echo "Step 2: Installing openclaw-deploy tool..."
echo "------------------------------------------"

if [ -d "openclaw-cli" ]; then
    print_info "Installing from local directory: openclaw-cli/"

    # Try to install with pip
    if pip3 install -e openclaw-cli/ &> /dev/null; then
        print_success "openclaw-deploy installed successfully"
    else
        print_warning "Standard installation failed, will use direct Python execution"
        # Create a wrapper script for direct execution
        cat > /tmp/openclaw-deploy << 'EOF'
#!/bin/bash
cd "$(dirname "$0")" && python3 -m openclaw_deploy.cli "$@"
EOF
        chmod +x /tmp/openclaw-deploy
        print_info "Created temporary wrapper script"
    fi
else
    print_error "openclaw-cli directory not found"
    echo "Please run this script from the agiens-test directory"
    exit 1
fi

echo ""

# Step 3: Run deployment
echo "Step 3: Running OpenClaw deployment..."
echo "------------------------------------------"
echo ""

# Check if openclaw-deploy command is available
if command -v openclaw-deploy &> /dev/null; then
    print_info "Running: openclaw-deploy deploy"
    openclaw-deploy deploy --verbose
elif [ -f "/tmp/openclaw-deploy" ]; then
    print_info "Running deployment using direct Python execution"
    cd openclaw-cli && python3 -m openclaw_deploy.cli deploy --verbose
else
    print_error "Could not find openclaw-deploy command"
    print_info "Try running manually: cd openclaw-cli && python3 -m openclaw_deploy.cli deploy"
    exit 1
fi

echo ""
echo "=========================================="
print_success "Setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Access OpenClaw at http://localhost:18789"
echo "  - Check status: openclaw-deploy status"
echo "  - View logs: openclaw-deploy logs --follow"
echo "  - Clean up: openclaw-deploy cleanup"
echo ""
