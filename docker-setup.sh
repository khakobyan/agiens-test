#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# OpenClaw Docker Setup Script
# Automates the full deployment: prereq check, build, onboard, and start.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# -----------------------------------------------------------------------------
# 1. Check prerequisites
# -----------------------------------------------------------------------------
check_prerequisites() {
    local missing=0

    if ! command -v docker &>/dev/null; then
        error "Docker is not installed. Install it from https://docs.docker.com/get-docker/"
        missing=1
    fi

    if ! docker compose version &>/dev/null; then
        error "Docker Compose V2 is not available. Update Docker or install the compose plugin."
        missing=1
    fi

    if ! docker info &>/dev/null 2>&1; then
        error "Docker daemon is not running. Start Docker and try again."
        missing=1
    fi

    if [ "$missing" -ne 0 ]; then
        exit 1
    fi

    info "All prerequisites satisfied."
}

# -----------------------------------------------------------------------------
# 2. Create host directories
# -----------------------------------------------------------------------------
create_directories() {
    info "Creating host directories for persistence..."
    mkdir -p "$HOME/.openclaw"
    mkdir -p "$HOME/openclaw/workspace"
    info "Created ~/.openclaw and ~/openclaw/workspace"
}

# -----------------------------------------------------------------------------
# 3. Set up environment file
# -----------------------------------------------------------------------------
setup_env() {
    if [ -f "$ENV_FILE" ]; then
        info ".env file already exists, keeping current configuration."
        return
    fi

    if [ ! -f "$ENV_EXAMPLE" ]; then
        error ".env.example not found. Are you running this from the project root?"
        exit 1
    fi

    info "Creating .env from .env.example..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    # Generate a random gateway token
    local token
    token=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | od -An -tx1 | tr -d ' \n')
    sed -i "s/^OPENCLAW_GATEWAY_TOKEN=$/OPENCLAW_GATEWAY_TOKEN=${token}/" "$ENV_FILE"

    info "Generated gateway authentication token."
    warn "Edit .env to add your model provider API keys before starting."
}

# -----------------------------------------------------------------------------
# 4. Build the Docker image
# -----------------------------------------------------------------------------
build_image() {
    info "Building OpenClaw Docker image (this may take several minutes)..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" build
    info "Docker image built successfully."
}

# -----------------------------------------------------------------------------
# 5. Start services
# -----------------------------------------------------------------------------
start_services() {
    info "Starting OpenClaw services..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d
    info "Services started."
}

# -----------------------------------------------------------------------------
# 6. Wait for healthy status
# -----------------------------------------------------------------------------
wait_for_healthy() {
    info "Waiting for gateway to become healthy..."
    local retries=20
    local wait_seconds=5

    for i in $(seq 1 $retries); do
        local status
        status=$(docker inspect --format='{{.State.Health.Status}}' openclaw-gateway 2>/dev/null || echo "not_found")

        if [ "$status" = "healthy" ]; then
            info "Gateway is healthy!"
            return 0
        fi

        echo -n "."
        sleep "$wait_seconds"
    done

    echo
    warn "Gateway did not become healthy within expected time."
    warn "Check logs with: docker compose logs openclaw-gateway"
    return 1
}

# -----------------------------------------------------------------------------
# 7. Print access info
# -----------------------------------------------------------------------------
print_access_info() {
    # shellcheck disable=SC1090
    source "$ENV_FILE"

    echo
    echo "=============================================="
    echo " OpenClaw is running!"
    echo "=============================================="
    echo
    echo " Web UI:  http://localhost:18789"

    if [ -n "${OPENCLAW_GATEWAY_TOKEN:-}" ]; then
        echo " Token:   ${OPENCLAW_GATEWAY_TOKEN}"
        echo
        echo " Full URL:"
        echo "   http://localhost:18789?token=${OPENCLAW_GATEWAY_TOKEN}"
    fi

    echo
    echo " Useful commands:"
    echo "   docker compose logs -f             # Follow logs"
    echo "   docker compose ps                  # Check status"
    echo "   docker compose down                # Stop services"
    echo "   docker compose run --rm openclaw-cli status  # Admin CLI"
    echo
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
main() {
    echo
    info "=== OpenClaw Docker Setup ==="
    echo

    check_prerequisites
    create_directories
    setup_env
    build_image
    start_services
    wait_for_healthy || true
    print_access_info
}

main "$@"
