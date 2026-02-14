# OpenClaw Self-Deployment Integration Guide

This guide explains how OpenClaw can deploy itself using the integrated openclaw-deploy automation tool.

## Overview

The self-deployment integration allows OpenClaw to:
- Deploy new instances of itself autonomously
- Support recursive deployment (deployed instances can deploy more instances)
- Operate in Docker-in-Docker scenarios
- Provide both CLI and API interfaces for deployment

## Architecture

### Integration Layers

The self-deployment capability is implemented in three layers:

#### Layer 1: Docker Image Integration
The Dockerfile is enhanced to include:
- **Python 3** and **pip** for running the openclaw-deploy tool
- **openclaw-deploy** installed from the local `openclaw-cli/` directory
- **Docker CLI** for Docker-in-Docker operations
- **openclaw-self-deploy** script installed to `/usr/local/bin/`

```dockerfile
# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip docker.io

# Install openclaw-deploy tool
COPY openclaw-cli /tmp/openclaw-cli
RUN pip3 install --no-cache-dir --break-system-packages /tmp/openclaw-cli

# Install self-deploy script
COPY scripts/self-deploy.sh /usr/local/bin/openclaw-self-deploy
```

#### Layer 2: Shell Script Interface
The `openclaw-self-deploy` script provides a user-friendly CLI interface:

```bash
openclaw-self-deploy [OPTIONS]

Options:
  --target-dir DIR        # Deployment directory
  --api-key KEY          # Anthropic API key
  --gateway-token TOKEN  # Gateway auth token
  --gateway-port PORT    # Gateway port (default: 18790)
  --no-interactive       # Non-interactive mode
```

The script:
1. Validates prerequisites (Docker, git, openclaw-deploy)
2. Clones the deployment repository
3. Prepares configuration
4. Executes deployment via openclaw-deploy
5. Provides status and next steps

#### Layer 3: API Endpoint (Optional)
Example API endpoint integration for programmatic access:

```javascript
POST /api/deploy
{
  "apiKey": "sk-ant-xxx",
  "gatewayPort": "18790"
}
```

See `integration-examples/api-endpoint.js` for implementation details.

## How It Works

### Deployment Flow

```
User/API Request
       ↓
openclaw-self-deploy script
       ↓
├─→ Check prerequisites
├─→ Clone repository to target directory
├─→ Prepare configuration (port, tokens, etc.)
├─→ Execute openclaw-deploy
│   ├─→ Create directories
│   ├─→ Generate .env
│   ├─→ Build Docker image
│   ├─→ Start services
│   ├─→ Configure gateway
│   └─→ Verify health
└─→ Show deployment info
```

### Docker-in-Docker

The integration uses Docker-in-Docker (DinD) to allow OpenClaw to manage Docker containers:

```yaml
# docker-compose.yml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

**How it works:**
1. The OpenClaw container mounts the host's Docker socket
2. When openclaw-self-deploy runs, it uses this socket to:
   - Clone the repository
   - Build new Docker images
   - Start new containers
3. New containers run alongside the original OpenClaw container

**Security Note:** Mounting the Docker socket gives the container significant privileges. Only enable this for trusted deployments.

### Port Management

Each deployment uses a different port to avoid conflicts:

- **Original instance:** Port 18789 (default)
- **First deployment:** Port 18790 (script default)
- **Additional deployments:** Specify custom ports

The script automatically modifies `docker-compose.yml` to use the specified port.

## Usage Examples

### Example 1: Basic Self-Deployment

Deploy a new OpenClaw instance from within a running container:

```bash
# Access the OpenClaw container
docker compose exec openclaw-gateway bash

# Deploy a new instance
openclaw-self-deploy

# Follow the interactive prompts
# Or use non-interactive mode:
openclaw-self-deploy --gateway-port 18790 --no-interactive
```

### Example 2: Deployment with API Key

Deploy with pre-configured API key:

```bash
openclaw-self-deploy \
  --api-key "sk-ant-your-anthropic-key" \
  --gateway-token "secure-token-123" \
  --gateway-port 18790 \
  --no-interactive
```

### Example 3: Custom Target Directory

Deploy to a specific location:

```bash
openclaw-self-deploy \
  --target-dir /home/node/deployments/instance-2 \
  --gateway-port 18791
```

### Example 4: Recursive Deployment

Deploy from a deployed instance:

```bash
# First deployment
docker compose exec openclaw-gateway openclaw-self-deploy --gateway-port 18790 --no-interactive

# Find the new container
NEW_CONTAINER=$(docker ps --filter "ancestor=openclaw:local" --format "{{.Names}}" | tail -1)

# Deploy from the new instance
docker exec $NEW_CONTAINER openclaw-self-deploy --gateway-port 18791 --no-interactive
```

### Example 5: API Endpoint Usage

If you've integrated the API endpoint:

```bash
curl -X POST http://localhost:18789/api/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "apiKey": "sk-ant-xxx",
    "gatewayPort": "18791",
    "targetDir": "/tmp/openclaw-new"
  }'
```

## Integration Patterns

### Pattern 1: Development Testing

Use self-deployment to test changes in isolation:

```bash
# Deploy a test instance
openclaw-self-deploy \
  --target-dir /tmp/openclaw-test \
  --gateway-port 19000 \
  --no-interactive

# Test changes in the new instance
# When done, clean up
openclaw-deploy --project-dir /tmp/openclaw-test cleanup --all
```

### Pattern 2: Multi-Tenant Setup

Deploy separate instances for different users/projects:

```bash
# User 1 instance
openclaw-self-deploy \
  --target-dir /opt/openclaw/user1 \
  --gateway-port 18801 \
  --gateway-token "user1-token" \
  --no-interactive

# User 2 instance
openclaw-self-deploy \
  --target-dir /opt/openclaw/user2 \
  --gateway-port 18802 \
  --gateway-token "user2-token" \
  --no-interactive
```

### Pattern 3: Staging Environment

Create a staging environment from production:

```bash
openclaw-self-deploy \
  --target-dir /opt/openclaw-staging \
  --gateway-port 18790 \
  --gateway-token "staging-token" \
  --no-interactive
```

### Pattern 4: Automated Scaling

Script multiple deployments for load distribution:

```bash
#!/bin/bash
# deploy-fleet.sh - Deploy multiple OpenClaw instances

START_PORT=18800
COUNT=5

for i in $(seq 1 $COUNT); do
    PORT=$((START_PORT + i))
    openclaw-self-deploy \
      --target-dir /opt/openclaw/instance-$i \
      --gateway-port $PORT \
      --no-interactive &
done

wait
echo "Deployed $COUNT instances"
```

## Extending the Integration

### Adding Custom Commands

To add self-deployment as an OpenClaw CLI command:

1. **Locate OpenClaw's CLI handler** (typically in `src/cli/` or similar)

2. **Add a new command:**

```javascript
// src/cli/commands/deploy.js
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

module.exports = {
  name: 'deploy-self',
  description: 'Deploy a new OpenClaw instance',
  options: [
    { flag: '--port <port>', description: 'Gateway port for new instance' },
    { flag: '--api-key <key>', description: 'API key for new instance' }
  ],
  async action(options) {
    const args = [];
    if (options.port) args.push(`--gateway-port ${options.port}`);
    if (options.apiKey) args.push(`--api-key ${options.apiKey}`);
    args.push('--no-interactive');

    const cmd = `openclaw-self-deploy ${args.join(' ')}`;
    const { stdout, stderr } = await execAsync(cmd);

    console.log(stdout);
    if (stderr) console.error(stderr);
  }
};
```

3. **Register the command** in OpenClaw's CLI registry

4. **Use it:**
```bash
node dist/index.js deploy-self --port 18790
```

### Creating a Web UI

Add a deployment interface to OpenClaw's web UI:

```html
<!-- Add to OpenClaw's control panel -->
<div class="deploy-section">
  <h3>Self-Deployment</h3>
  <form id="deploy-form">
    <input type="number" name="port" placeholder="Gateway Port" value="18790">
    <input type="password" name="apiKey" placeholder="API Key (optional)">
    <button type="submit">Deploy New Instance</button>
  </form>
  <div id="deploy-status"></div>
</div>

<script>
document.getElementById('deploy-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);

  const response = await fetch('/api/deploy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      gatewayPort: formData.get('port'),
      apiKey: formData.get('apiKey')
    })
  });

  const result = await response.json();
  document.getElementById('deploy-status').textContent =
    result.success ? 'Deployment started!' : 'Deployment failed: ' + result.error;
});
</script>
```

### Plugin Architecture

If OpenClaw supports plugins, create a self-deployment plugin:

```javascript
// plugins/self-deploy/index.js
module.exports = {
  name: 'self-deploy',
  version: '1.0.0',

  // Register commands
  commands: [{
    name: 'deploy-self',
    handler: require('./commands/deploy')
  }],

  // Register API endpoints
  routes: [{
    method: 'POST',
    path: '/api/deploy',
    handler: require('./handlers/deploy')
  }],

  // Register UI components
  ui: {
    panels: [{
      location: 'admin',
      component: require('./components/DeployPanel')
    }]
  }
};
```

## Security Considerations

### 1. Docker Socket Access

Mounting the Docker socket gives significant privileges:

```yaml
# Production: Use read-only mount
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro

# Development: Full access if needed
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

**Alternatives:**
- Use Docker API over TCP with TLS
- Use Docker-in-Docker container (dind) instead of socket mounting
- Implement deployment through a separate privileged service

### 2. API Authentication

Always require authentication for deployment endpoints:

```javascript
app.post('/api/deploy', requireAuth, requireAdmin, handleDeploy);
```

### 3. Rate Limiting

Prevent abuse by limiting deployment frequency:

```javascript
const rateLimit = require('express-rate-limit');

const deployLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 3 // Limit each IP to 3 deployments per window
});

app.post('/api/deploy', deployLimiter, handleDeploy);
```

### 4. Input Validation

Validate all user inputs:

```javascript
function validateDeployParams(params) {
  const { gatewayPort, targetDir } = params;

  // Validate port number
  if (gatewayPort && !/^\d{4,5}$/.test(gatewayPort)) {
    throw new Error('Invalid port number');
  }

  // Prevent directory traversal
  if (targetDir && targetDir.includes('..')) {
    throw new Error('Invalid target directory');
  }

  // Add more validations as needed
}
```

### 5. Resource Limits

Prevent resource exhaustion:

```javascript
// Limit number of concurrent deployments
const MAX_CONCURRENT_DEPLOYS = 2;
let activeDeployments = 0;

async function handleDeploy(req, res) {
  if (activeDeployments >= MAX_CONCURRENT_DEPLOYS) {
    return res.status(429).json({
      error: 'Too many concurrent deployments'
    });
  }

  activeDeployments++;
  try {
    await executeDeploy(req.body);
  } finally {
    activeDeployments--;
  }
}
```

## Troubleshooting

See `TESTING.md` for comprehensive troubleshooting guide.

## Best Practices

1. **Always use non-interactive mode** in production/automation
2. **Specify unique ports** for each deployment
3. **Set API keys** during deployment to avoid manual configuration
4. **Monitor deployed instances** for health and resource usage
5. **Clean up failed deployments** using `openclaw-deploy cleanup`
6. **Use version tags** instead of `latest` for reproducible deployments
7. **Implement logging** to track all deployment attempts
8. **Set up alerts** for deployment failures

## Limitations

1. **Docker dependency:** Requires Docker socket access
2. **Network ports:** Each instance needs a unique port
3. **Resource usage:** Each instance consumes memory and CPU
4. **Storage:** Multiple deployments require significant disk space
5. **No orchestration:** For production clustering, consider Kubernetes

## Future Enhancements

Potential improvements to the integration:

1. **Kubernetes support:** Deploy to K8s clusters instead of Docker Compose
2. **Cloud provider integration:** Deploy to AWS ECS, GCP Cloud Run, etc.
3. **Service mesh:** Integrate with Istio or Linkerd for advanced networking
4. **Monitoring:** Built-in Prometheus metrics and Grafana dashboards
5. **Auto-scaling:** Automatically deploy/remove instances based on load
6. **Health management:** Automatic restart of failed instances
7. **Load balancing:** Distribute requests across multiple instances
8. **Configuration management:** Centralized config for all instances

## Contributing

To improve this integration:

1. Test with different OpenClaw versions
2. Add support for additional deployment targets
3. Improve error handling and recovery
4. Enhance security features
5. Create additional integration examples

## Support

For issues or questions:
- Check `TESTING.md` for testing procedures
- Review `api-endpoint.js` for API examples
- See main `README.md` for general documentation
