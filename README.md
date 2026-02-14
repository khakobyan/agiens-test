# OpenClaw Docker Deployment

Production-ready Docker setup for [OpenClaw](https://github.com/openclaw/openclaw), the open-source personal AI agent.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) V2
- At least one model provider API key (Anthropic, OpenAI, Google AI, or a local Ollama instance)

## Getting Started

### First Time Setup
```bash
# 1. Clone the repository
git clone https://github.com/khakobyan/agiens-test.git
cd agiens-test

# 2. Run automated setup
./setup.sh

# 3. Add your API key to .env
nano .env  # or use your preferred editor
# Add: ANTHROPIC_API_KEY=sk-ant-your-key-here

# 4. Restart to apply API key
openclaw-deploy update

# 5. Access OpenClaw
# Open: http://localhost:18789
```

### ⚠️ Important: API Keys Required

OpenClaw needs at least ONE model provider API key to function:
- **Anthropic Claude:** Get key from https://console.anthropic.com/
- **OpenAI:** Get key from https://platform.openai.com/
- **Google AI:** Get key from https://ai.google.dev/
- **Ollama (local):** Install from https://ollama.ai/

Without an API key, the gateway will start but won't be able to process requests.

## Quick Start

**Already cloned the repo?** Skip to [Option 1](#option-1-automated-setup-recommended)  
**First time?** See [Getting Started](#getting-started) above.

### Option 1: Automated Setup (Recommended)

One-command setup using the deployment automation tool:

```bash
./setup.sh
```

This script will:
1. Check all prerequisites (Docker, Docker Compose, Python, disk space)
2. Install the `openclaw-deploy` automation tool
3. Run the automated deployment workflow:
   - Create persistence directories (`~/.openclaw`, `~/openclaw/workspace`)
   - Generate `.env` file with a random gateway token
   - Build the Docker image
   - Start the services
   - Configure OpenClaw gateway (local mode + auth token)
   - Verify deployment health
   - Print access information

After successful deployment, edit `.env` to add your API key(s), then restart:

```bash
openclaw-deploy update
# or
docker compose restart
```

### Option 2: Manual Docker Setup

```bash
./docker-setup.sh
```

This basic script will:
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

## Deployment Automation Tool

The `openclaw-deploy` CLI tool provides production-ready automation for OpenClaw deployments with intelligent rollback, health verification, and comprehensive error handling.

### Installation

```bash
# Install from source
pip install -e openclaw-cli/

# Or use directly without installation
cd openclaw-cli && python -m openclaw_deploy.cli --help
```

### Usage

```bash
# Deploy OpenClaw
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

See [openclaw-cli/README.md](openclaw-cli/README.md) for complete documentation.

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

---

## ✅ Step 3: OpenClaw Self-Deployment Integration

**Status:** COMPLETED

OpenClaw can now deploy itself using the integrated openclaw-deploy automation tool!

### 🎯 What's New

The Docker image now includes:
- **Python 3 and pip** - Runtime for openclaw-deploy
- **openclaw-deploy tool** - Full automation CLI installed from openclaw-cli/
- **Docker CLI** - For Docker-in-Docker operations
- **openclaw-self-deploy script** - Easy-to-use deployment interface at `/usr/local/bin/`

### 🚀 Self-Deployment Capabilities

OpenClaw can now:
1. ✅ Deploy new instances of itself from within the container
2. ✅ Support recursive deployment (deployed instances can deploy more)
3. ✅ Run in Docker-in-Docker scenarios
4. ✅ Provide both CLI and API interfaces for deployment

### Quick Start: Self-Deployment

```bash
# 1. Build the enhanced image (if not already built)
docker compose build --no-cache

# 2. Start OpenClaw
docker compose up -d

# 3. Access the container
docker compose exec openclaw-gateway bash

# 4. Deploy a new instance
openclaw-self-deploy --gateway-port 18790 --no-interactive

# 5. Exit and verify
exit
docker ps | grep openclaw  # Should see two containers
curl http://localhost:18790/health  # New instance running!
```

### 📖 Usage Examples

#### Basic Interactive Deployment
```bash
docker compose exec openclaw-gateway openclaw-self-deploy
```

#### Non-Interactive with Custom Port
```bash
docker compose exec openclaw-gateway openclaw-self-deploy \
  --gateway-port 18790 \
  --no-interactive
```

#### With Pre-Configured API Key
```bash
docker compose exec openclaw-gateway openclaw-self-deploy \
  --api-key "sk-ant-your-anthropic-key" \
  --gateway-token "secure-token-123" \
  --gateway-port 18790 \
  --no-interactive
```

#### Custom Target Directory
```bash
docker compose exec openclaw-gateway openclaw-self-deploy \
  --target-dir /tmp/openclaw-staging \
  --gateway-port 18791
```

#### Get Help
```bash
docker compose exec openclaw-gateway openclaw-self-deploy --help
```

### 🔌 API Endpoint Integration (Optional)

For programmatic deployment, integrate the API endpoint:

```bash
# Example API call
curl -X POST http://localhost:18789/api/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "apiKey": "sk-ant-xxx",
    "gatewayPort": "18791",
    "targetDir": "/tmp/openclaw-new"
  }'
```

See `integration-examples/api-endpoint.js` for complete implementation.

### 🏗️ Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│              OpenClaw Container                          │
│                                                          │
│  ┌──────────────┐      ┌──────────────────┐            │
│  │  OpenClaw    │      │ openclaw-deploy  │            │
│  │   Node.js    │──────│  Python CLI      │            │
│  │              │      │                  │            │
│  └──────────────┘      └─────────┬────────┘            │
│                                   │                     │
│  ┌──────────────────────────────┴─────┐               │
│  │  openclaw-self-deploy              │               │
│  │  Shell Script Wrapper              │               │
│  └────────────────────┬───────────────┘               │
│                        │                               │
│                        │  Uses Docker Socket           │
│                        ▼                               │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  New OpenClaw Instance│
              │  (Self-Deployed)      │
              └──────────────────────┘
```

### 📚 Documentation

Comprehensive guides in `integration-examples/`:

| Document | Description |
|----------|-------------|
| **[README.md](integration-examples/README.md)** | Overview and quick start |
| **[INTEGRATION.md](integration-examples/INTEGRATION.md)** | Complete integration guide with patterns and examples |
| **[TESTING.md](integration-examples/TESTING.md)** | Testing procedures and troubleshooting |
| **[api-endpoint.js](integration-examples/api-endpoint.js)** | Example API endpoint implementation |

### ✨ Key Features

#### 1. Multi-Layer Integration
- **Layer 1:** Docker image includes Python, openclaw-deploy, and Docker CLI
- **Layer 2:** Shell script wrapper (`openclaw-self-deploy`) provides user-friendly interface
- **Layer 3:** API endpoint example for programmatic deployment

#### 2. Docker-in-Docker Support
- Mounts Docker socket: `/var/run/docker.sock:/var/run/docker.sock:ro`
- Handles port conflicts automatically
- Supports concurrent deployments
- Works with existing Docker daemon

#### 3. Comprehensive Error Handling
- Prerequisite validation (Docker, git, disk space)
- Automatic rollback on deployment failure
- Detailed logging with color-coded output
- Clear error messages and next steps

#### 4. Recursive Deployment
- Deployed instances can deploy more instances
- Multi-tier deployment support
- Useful for testing and multi-tenant setups
- No limit on deployment depth

### 🛡️ Security Considerations

⚠️ **Important:** Docker socket mount gives significant privileges

**Recommendations:**
- Use read-only mount: `/var/run/docker.sock:/var/run/docker.sock:ro`
- Only enable in trusted environments
- Implement authentication on API endpoints
- Add rate limiting for deployment requests
- Validate all inputs
- Monitor resource usage
- Log all deployment attempts

**Production Setup:**
```javascript
// Example: Secure API endpoint
app.post('/api/deploy',
  requireAuth,        // Authentication
  requireAdmin,       // Authorization
  deployRateLimiter,  // Rate limiting
  validateInputs,     // Input validation
  handleSelfDeploy    // Deployment handler
);
```

### 🧪 Testing

Quick verification:
```bash
# 1. Build image with integration
docker compose build --no-cache
docker compose up -d

# 2. Test self-deployment
docker compose exec openclaw-gateway openclaw-self-deploy \
  --gateway-port 18790 --no-interactive

# 3. Verify both instances running
docker ps | grep openclaw

# 4. Check new instance health
curl http://localhost:18790/health

# 5. View deployment logs
openclaw-deploy --project-dir /tmp/openclaw-deploy logs
```

For comprehensive testing, see: [integration-examples/TESTING.md](integration-examples/TESTING.md)

### 💡 Use Cases

1. **Development Testing**
   ```bash
   openclaw-self-deploy --target-dir /tmp/test --gateway-port 19000 --no-interactive
   ```

2. **Multi-Tenant Setup**
   ```bash
   # User 1
   openclaw-self-deploy --target-dir /opt/user1 --gateway-port 18801 --no-interactive
   # User 2
   openclaw-self-deploy --target-dir /opt/user2 --gateway-port 18802 --no-interactive
   ```

3. **Staging Environment**
   ```bash
   openclaw-self-deploy --target-dir /opt/staging --gateway-port 18790 --no-interactive
   ```

4. **Automated Fleet Deployment**
   ```bash
   for port in 18800 18801 18802; do
     openclaw-self-deploy --gateway-port $port --no-interactive &
   done
   wait
   ```

### 📦 What's Included

- ✅ **Modified Dockerfile** - Includes Python, pip, openclaw-deploy, Docker CLI
- ✅ **Self-Deploy Script** - `scripts/self-deploy.sh` with comprehensive features
- ✅ **Updated docker-compose.yml** - Docker socket mount for DinD support
- ✅ **Integration Examples** - API endpoint, usage patterns, best practices
- ✅ **Comprehensive Documentation** - Integration guide, testing guide, troubleshooting
- ✅ **Security Guidelines** - Authentication, validation, rate limiting

### 🎯 Next Steps

1. **Read the integration guide**
   ```bash
   cat integration-examples/INTEGRATION.md
   ```

2. **Test self-deployment**
   ```bash
   cat integration-examples/TESTING.md
   ```

3. **Implement API endpoint** (optional)
   - Use `integration-examples/api-endpoint.js` as template
   - Add authentication and authorization
   - Implement rate limiting

4. **Customize for your needs**
   - Adapt examples to your use case
   - Add monitoring and alerting
   - Set up centralized logging

### 🔧 Technical Details

**Modified Files:**
- `Dockerfile` - Added Python, openclaw-deploy, Docker CLI, self-deploy script
- `docker-compose.yml` - Added Docker socket mount
- `scripts/self-deploy.sh` - Main self-deployment script (NEW)
- `integration-examples/` - Documentation and code examples (NEW)

**Integration Points:**
- CLI: `openclaw-self-deploy` command available in container
- API: Example endpoint in `integration-examples/api-endpoint.js`
- Direct: Use `openclaw-deploy` Python CLI directly

**Requirements:**
- Docker socket access (via mount)
- Python 3.x (included in image)
- Git (included in image)
- Sufficient disk space for multiple deployments

### 📊 Performance

Typical deployment time: **2-5 minutes**

Factors affecting performance:
- Network speed (cloning repository)
- Docker build cache
- System resources (CPU, memory, disk)
- Number of concurrent deployments

Resource usage per instance:
- **CPU:** ~0.5-1.0 cores
- **Memory:** ~512MB-1GB
- **Disk:** ~2-3GB (including image and volumes)

### 🌟 Future Enhancements

Potential improvements:
- Kubernetes deployment support
- Cloud provider integration (AWS ECS, GCP Cloud Run)
- Auto-scaling based on load
- Built-in monitoring and metrics
- Load balancer integration
- Service mesh support (Istio, Linkerd)

### 📞 Support

For questions or issues with self-deployment:

1. **Check the testing guide:** `integration-examples/TESTING.md`
2. **Review integration patterns:** `integration-examples/INTEGRATION.md`
3. **Examine API examples:** `integration-examples/api-endpoint.js`
4. **Check troubleshooting section** in testing guide

---

## Summary of Deployment Steps (All 3 Steps)

### Step 1: Manual Docker Deployment ✅
```bash
./docker-setup.sh  # Basic Docker deployment
```

### Step 2: Automated Deployment Tool ✅
```bash
./setup.sh  # Installs and runs openclaw-deploy
# or
openclaw-deploy deploy  # Direct CLI usage
```

### Step 3: Self-Deployment Integration ✅
```bash
# From within OpenClaw container
openclaw-self-deploy --gateway-port 18790 --no-interactive
```

**All three deployment methods are now available!** 🎉
