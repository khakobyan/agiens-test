# OpenClaw Docker Deployment

Production-ready Docker setup for [OpenClaw](https://github.com/openclaw/openclaw), the open-source personal AI agent.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) V2
- At least one model provider API key (Anthropic, OpenAI, Google AI, or a local Ollama instance)

## Quick Start

```bash
./docker-setup.sh
```

This script will:
1. Verify Docker prerequisites
2. Create persistence directories (`~/.openclaw`, `~/openclaw/workspace`)
3. Generate a `.env` file with a random gateway token
4. Build the Docker image
5. Start the services
6. Print the access URL

After running, edit `.env` to add your API key(s), then restart:

```bash
docker compose restart
```

## Manual Setup

```bash
# 1. Create environment config
cp .env.example .env
# Edit .env — add API keys and set OPENCLAW_GATEWAY_TOKEN

# 2. Create host directories
mkdir -p ~/.openclaw ~/openclaw/workspace

# 3. Build and start
docker compose up -d --build

# 4. Verify
docker compose ps
docker compose logs -f openclaw-gateway
```

Access the web UI at `http://localhost:18789?token=<your-token>`.

## Configuration

All settings are in `.env`. See `.env.example` for the full reference. Key variables:

| Variable | Description | Default |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | Auth token for web UI access | *(generated)* |
| `OPENCLAW_GATEWAY_BIND` | Network bind mode | `lan` |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `GOOGLE_AI_API_KEY` | Google AI (Gemini) API key | — |
| `OLLAMA_BASE_URL` | Ollama server URL for local models | — |
| `OPENCLAW_DOCKER_APT_PACKAGES` | Extra system packages (build-time) | — |
| `OPENCLAW_HOME_VOLUME` | Named volume for /home/node | `openclaw-home` |

## Architecture

| Service | Purpose | Port |
|---|---|---|
| `openclaw-gateway` | Main agent runtime + web UI | 18789 |
| `openclaw-cli` | Admin CLI (runs on demand) | — |

### Persistence

| Host Path | Container Path | Contents |
|---|---|---|
| `~/.openclaw` | `/home/node/.openclaw` | Configuration, memory, API keys |
| `~/openclaw/workspace` | `/home/node/.openclaw/workspace` | Files accessible to the agent |
| Named volume `openclaw-home` | `/home/node` | Node.js home directory |

## Common Operations

```bash
# View logs
docker compose logs -f openclaw-gateway

# Check health status
docker compose ps

# Run admin CLI
docker compose run --rm openclaw-cli status

# Open a shell in the gateway container
docker compose exec openclaw-gateway bash

# Open a root shell (for package installation)
docker compose exec -u root openclaw-gateway bash

# Stop services
docker compose down

# Rebuild after configuration changes
docker compose up -d --build

# Update to latest OpenClaw
docker compose build --no-cache
docker compose up -d
```

## Security

This setup follows security best practices:

- **Non-root execution:** Runs as `node` user (uid 1000)
- **Read-only root filesystem:** Only `/tmp` is writable via tmpfs
- **No new privileges:** `no-new-privileges` security option enabled
- **Token authentication:** Web UI requires a token to access
- **Log rotation:** JSON file logging with 10MB max size, 3 file rotation
- **Minimal base image:** `node:22-bookworm-slim` with only required packages

## Troubleshooting

**Permission errors on Linux:**
```bash
sudo chown -R 1000:1000 ~/.openclaw ~/openclaw/workspace
```

**Gateway not becoming healthy:**
```bash
docker compose logs openclaw-gateway
# Check if API keys are configured in .env
```

**Build failures with native modules:**
```bash
# Rebuild with clean cache
docker compose build --no-cache
```

**Port 18789 already in use:**
```bash
# Change the host port in docker-compose.yml
# e.g., "8080:18789" to access via port 8080
```
