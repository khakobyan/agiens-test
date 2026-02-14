#!/bin/bash
# =============================================================================
# OpenClaw Self-Deployment Script
# =============================================================================
# This script allows OpenClaw to deploy another instance of itself using the
# openclaw-deploy automation tool. It handles Docker-in-Docker scenarios and
# provides comprehensive error handling and logging.
#
# Usage:
#   openclaw-self-deploy [OPTIONS]
#
# Options:
#   --target-dir DIR        Target deployment directory (default: /tmp/openclaw-deploy)
#   --api-key KEY          Anthropic API key for new instance
#   --gateway-token TOKEN  Gateway token for new instance
#   --gateway-port PORT    Gateway port for new instance (default: 18790)
#   --no-interactive       Run without user prompts
#   --help                 Show this help message
#
# Examples:
#   # Deploy with prompts
#   openclaw-self-deploy
#
#   # Non-interactive deployment
#   openclaw-self-deploy --api-key sk-ant-xxx --no-interactive
#
#   # Deploy to custom port
#   openclaw-self-deploy --gateway-port 8080
# =============================================================================

set -euo pipefail

# Default values
TARGET_DIR="/tmp/openclaw-deploy"
API_KEY=""
GATEWAY_TOKEN=""
GATEWAY_PORT="18790"
INTERACTIVE=true
REPO_URL="https://github.com/khakobyan/agiens-test.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    head -n 30 "$0" | grep "^#" | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --target-dir)
                TARGET_DIR="$2"
                shift 2
                ;;
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --gateway-token)
                GATEWAY_TOKEN="$2"
                shift 2
                ;;
            --gateway-port)
                GATEWAY_PORT="$2"
                shift 2
                ;;
            --no-interactive)
                INTERACTIVE=false
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if openclaw-deploy is installed
    if ! command -v openclaw-deploy &> /dev/null; then
        log_error "openclaw-deploy is not installed"
        log_info "Installing openclaw-deploy..."
        pip3 install --break-system-packages openclaw-deploy || {
            log_error "Failed to install openclaw-deploy"
            exit 1
        }
    fi

    # Check if Docker is accessible
    if ! docker info &> /dev/null; then
        log_error "Cannot access Docker daemon"
        log_warning "Make sure Docker socket is mounted: -v /var/run/docker.sock:/var/run/docker.sock"
        exit 1
    fi

    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# Clone deployment repository
clone_repository() {
    log_info "Setting up deployment directory: $TARGET_DIR"

    # Remove existing directory if it exists
    if [ -d "$TARGET_DIR" ]; then
        log_warning "Target directory exists, removing..."
        rm -rf "$TARGET_DIR"
    fi

    # Clone the repository
    log_info "Cloning deployment repository..."
    git clone --depth 1 "$REPO_URL" "$TARGET_DIR" || {
        log_error "Failed to clone repository"
        exit 1
    }

    cd "$TARGET_DIR"
    log_success "Repository cloned successfully"
}

# Prepare deployment configuration
prepare_deployment() {
    log_info "Preparing deployment configuration..."

    # Build openclaw-deploy arguments
    DEPLOY_ARGS=("deploy")

    # Add API key if provided
    if [ -n "$API_KEY" ]; then
        DEPLOY_ARGS+=("--api-key" "$API_KEY")
    fi

    # Add gateway token if provided
    if [ -n "$GATEWAY_TOKEN" ]; then
        DEPLOY_ARGS+=("--gateway-token" "$GATEWAY_TOKEN")
    fi

    # Add non-interactive flag if specified
    if [ "$INTERACTIVE" = false ]; then
        DEPLOY_ARGS+=("--no-interactive")
    fi

    # Port conflict handling: update docker-compose.yml to use different port
    if [ "$GATEWAY_PORT" != "18789" ]; then
        log_info "Configuring custom gateway port: $GATEWAY_PORT"
        sed -i "s/\"18789:18789\"/\"${GATEWAY_PORT}:18789\"/" docker-compose.yml
    fi

    log_success "Configuration prepared"
}

# Execute deployment
execute_deployment() {
    log_info "Starting OpenClaw deployment..."
    log_info "This may take several minutes..."

    # Run openclaw-deploy
    if openclaw-deploy --project-dir "$TARGET_DIR" "${DEPLOY_ARGS[@]}"; then
        log_success "Deployment completed successfully!"
        show_deployment_info
        return 0
    else
        log_error "Deployment failed"
        log_info "Check logs at: $TARGET_DIR"
        return 1
    fi
}

# Show deployment information
show_deployment_info() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         OpenClaw Self-Deployment Successful! 🦞            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Deployment Details:"
    echo "  • Location: $TARGET_DIR"
    echo "  • Gateway URL: http://localhost:$GATEWAY_PORT"
    echo "  • Container: openclaw-gateway"
    echo ""
    log_info "Next Steps:"
    echo "  1. Add API keys to: $TARGET_DIR/.env"
    echo "  2. Restart services: cd $TARGET_DIR && docker compose restart"
    echo "  3. Check status: openclaw-deploy --project-dir $TARGET_DIR status"
    echo "  4. View logs: openclaw-deploy --project-dir $TARGET_DIR logs --follow"
    echo ""
}

# Cleanup on error
cleanup_on_error() {
    log_warning "Cleaning up due to error..."
    if [ -d "$TARGET_DIR" ]; then
        cd /
        # Don't remove the directory, keep it for debugging
        log_info "Deployment files preserved at: $TARGET_DIR"
    fi
}

# Main execution
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         OpenClaw Self-Deployment Tool 🦞                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    parse_args "$@"

    # Trap errors for cleanup
    trap cleanup_on_error ERR

    check_prerequisites
    clone_repository
    prepare_deployment
    execute_deployment

    log_success "All done! Your new OpenClaw instance is ready."
}

# Run main function
main "$@"
