# OpenClaw Self-Deployment Integration Examples

This directory contains examples and documentation for integrating self-deployment capabilities into OpenClaw.

## Overview

These examples demonstrate how OpenClaw can deploy itself using the openclaw-deploy automation tool. The integration is already built into the Docker image through modifications to the Dockerfile and docker-compose.yml.

## What's Included

### Documentation

- **[INTEGRATION.md](INTEGRATION.md)** - Comprehensive integration guide
  - Architecture overview
  - How the integration works
  - Usage examples
  - Extension patterns
  - Security considerations
  - Best practices

- **[TESTING.md](TESTING.md)** - Testing guide
  - Test scenarios
  - Verification procedures
  - Troubleshooting
  - Performance testing
  - Security testing

### Code Examples

- **[api-endpoint.js](api-endpoint.js)** - Example API endpoint implementation
  - Express.js handlers for deployment
  - Status checking endpoints
  - Example usage patterns

## Quick Start

### 1. Build the Enhanced Image

The Dockerfile already includes the self-deployment integration:

```bash
docker compose build --no-cache
docker compose up -d
```

### 2. Test Self-Deployment

Access the container and run the self-deploy script:

```bash
docker compose exec openclaw-gateway bash

# Inside the container
openclaw-self-deploy --help

# Deploy a new instance
openclaw-self-deploy --gateway-port 18790 --no-interactive
```

### 3. Verify the Deployment

```bash
# Check running containers
docker ps | grep openclaw

# Access the new instance
curl http://localhost:18790/health
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Container                       │
│                                                              │
│  ┌──────────────┐      ┌─────────────────┐                 │
│  │   OpenClaw   │      │ openclaw-deploy │                 │
│  │     App      │      │   Python CLI    │                 │
│  │              │      │                 │                 │
│  │ dist/index.js├─────→│ deploy.py       │                 │
│  │              │      │ status.py       │                 │
│  └──────────────┘      │ update.py       │                 │
│                        │ cleanup.py      │                 │
│  ┌──────────────┐      └────────┬────────┘                 │
│  │ self-deploy  │               │                           │
│  │   script     ├───────────────┘                           │
│  │              │                                           │
│  │ .sh wrapper  │      ┌─────────────────┐                 │
│  └──────┬───────┘      │  Docker Socket  │                 │
│         │              │   (mounted)     │                 │
│         └─────────────→│                 │                 │
│                        └─────────────────┘                 │
└────────────────────────────────┬───────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   New OpenClaw Instance│
                    │   (Self-Deployed)      │
                    └────────────────────────┘
```

## Key Components

### 1. Enhanced Dockerfile

The Dockerfile includes:
- Python 3 and pip
- openclaw-deploy tool (installed from openclaw-cli/)
- Docker CLI for Docker-in-Docker
- Self-deploy script at `/usr/local/bin/openclaw-self-deploy`

### 2. Self-Deploy Script

Located at: `/usr/local/bin/openclaw-self-deploy` in the container

Features:
- Interactive and non-interactive modes
- Port management
- API key configuration
- Error handling and rollback
- Comprehensive logging

### 3. Docker-in-Docker Support

The docker-compose.yml mounts the Docker socket:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

This allows the container to deploy new Docker containers.

## Usage Scenarios

### Scenario 1: Development Testing

```bash
# Deploy a test environment
docker compose exec openclaw-gateway openclaw-self-deploy \
  --target-dir /tmp/openclaw-test \
  --gateway-port 19000 \
  --no-interactive

# Test your changes
# ...

# Clean up when done
openclaw-deploy --project-dir /tmp/openclaw-test cleanup --all
```

### Scenario 2: Multi-Instance Setup

```bash
# Production instance (already running on 18789)
# Deploy development instance
openclaw-self-deploy --gateway-port 18790 --no-interactive

# Deploy staging instance
openclaw-self-deploy --gateway-port 18791 --no-interactive
```

### Scenario 3: Automated Deployment

```bash
# Create a deployment script
cat > deploy-fleet.sh << 'EOF'
#!/bin/bash
for port in 18800 18801 18802; do
    openclaw-self-deploy \
      --gateway-port $port \
      --target-dir /opt/openclaw-$port \
      --no-interactive &
done
wait
echo "Fleet deployed!"
EOF

chmod +x deploy-fleet.sh
docker compose exec openclaw-gateway ./deploy-fleet.sh
```

## API Integration

To add a deployment API endpoint to OpenClaw:

1. **Copy the example:**
   ```bash
   cp integration-examples/api-endpoint.js /path/to/openclaw/src/api/
   ```

2. **Integrate into your server:**
   ```javascript
   const { setupSelfDeploymentRoutes } = require('./api-endpoint');
   setupSelfDeploymentRoutes(app);
   ```

3. **Add authentication middleware:**
   ```javascript
   app.post('/api/deploy', requireAuth, requireAdmin, handleSelfDeploy);
   ```

4. **Use the API:**
   ```bash
   curl -X POST http://localhost:18789/api/deploy \
     -H "Content-Type: application/json" \
     -d '{"gatewayPort": "18790"}'
   ```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Docker Socket Access**
   - Mounting the Docker socket gives significant privileges
   - Only enable in trusted environments
   - Consider using read-only mount: `/var/run/docker.sock:/var/run/docker.sock:ro`

2. **API Endpoints**
   - Always require authentication
   - Implement rate limiting
   - Validate all inputs
   - Log all deployment attempts

3. **Resource Limits**
   - Limit concurrent deployments
   - Monitor disk space
   - Set container resource constraints

## Testing

Follow the comprehensive testing guide in [TESTING.md](TESTING.md):

1. Basic self-deployment
2. Custom parameters
3. Docker-in-Docker permissions
4. API endpoint testing
5. Recursive deployment
6. Error handling
7. Cleanup procedures

## Troubleshooting

### Can't access Docker

**Problem:** `Cannot access Docker daemon`

**Solution:**
```yaml
# Ensure docker-compose.yml has:
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Command not found

**Problem:** `openclaw-self-deploy: command not found`

**Solution:**
```bash
# Rebuild the image
docker compose build --no-cache
docker compose up -d
```

### Port conflicts

**Problem:** Port 18789 is already in use

**Solution:**
```bash
# Use a different port
openclaw-self-deploy --gateway-port 18800
```

## File Structure

```
integration-examples/
├── README.md              # This file
├── INTEGRATION.md         # Comprehensive integration guide
├── TESTING.md            # Testing procedures
└── api-endpoint.js       # Example API endpoint code
```

## Related Files

- `/scripts/self-deploy.sh` - The self-deployment script
- `/Dockerfile` - Enhanced with Python and openclaw-deploy
- `/docker-compose.yml` - Configured for Docker-in-Docker
- `/openclaw-cli/` - The openclaw-deploy Python tool

## Next Steps

1. **Read the integration guide:** [INTEGRATION.md](INTEGRATION.md)
2. **Test the integration:** [TESTING.md](TESTING.md)
3. **Implement API endpoints:** Use [api-endpoint.js](api-endpoint.js) as a template
4. **Customize for your needs:** Adapt the examples to your specific use case

## Contributing

Improvements welcome! Consider:
- Additional integration patterns
- More test scenarios
- Enhanced security features
- Performance optimizations
- Additional deployment targets (K8s, cloud providers)

## Support

For questions or issues:
1. Check [TESTING.md](TESTING.md) for common issues
2. Review [INTEGRATION.md](INTEGRATION.md) for detailed documentation
3. Examine the example code in [api-endpoint.js](api-endpoint.js)
4. Check the main project README

## License

Same as the main project - see LICENSE file in the root directory.
