# =============================================================================
# Stage 1: Build
# =============================================================================
FROM node:22-bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /build

# Clone OpenClaw source
ARG OPENCLAW_VERSION=latest
RUN git clone --depth 1 https://github.com/openclaw/openclaw.git . \
    && if [ "$OPENCLAW_VERSION" != "latest" ]; then \
         git fetch --depth 1 origin tag "$OPENCLAW_VERSION" && \
         git checkout "$OPENCLAW_VERSION"; \
       fi

# Install dependencies and build
RUN pnpm install --frozen-lockfile \
    && pnpm approve-builds \
    && pnpm build

ENV CI=true

# Prune dev dependencies for smaller runtime image
RUN pnpm prune --prod

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM node:22-bookworm-slim AS runtime

# Install optional runtime system packages
ARG OPENCLAW_DOCKER_APT_PACKAGES=""
RUN if [ -n "$OPENCLAW_DOCKER_APT_PACKAGES" ]; then \
      apt-get update && apt-get install -y --no-install-recommends \
        $OPENCLAW_DOCKER_APT_PACKAGES \
      && rm -rf /var/lib/apt/lists/*; \
    fi

# Install common runtime utilities including Python for openclaw-deploy
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Create app directory owned by node user
WORKDIR /app
RUN chown node:node /app

# Copy built application from builder stage
COPY --from=builder --chown=node:node /build /app

# Install openclaw-deploy tool for self-deployment capability
COPY openclaw-cli /tmp/openclaw-cli
RUN pip3 install --no-cache-dir --break-system-packages /tmp/openclaw-cli \
    && rm -rf /tmp/openclaw-cli

# Create self-deploy script
COPY scripts/self-deploy.sh /usr/local/bin/openclaw-self-deploy
RUN chmod +x /usr/local/bin/openclaw-self-deploy

# Create directories for persistence (will be mounted as volumes)
RUN mkdir -p /home/node/.openclaw /home/node/.openclaw/workspace \
    && chown -R node:node /home/node

# Switch to non-root user
USER node

# Gateway control UI port
EXPOSE 18789

# Health check: verify gateway is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:18789/health || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command: start the gateway
CMD ["node", "dist/index.js", "gateway", "--bind", "lan"]
