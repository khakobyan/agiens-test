# Testing OpenClaw Self-Deployment Integration

This guide provides comprehensive testing instructions for the OpenClaw self-deployment integration.

## Prerequisites

Before testing, ensure you have:

1. Docker and Docker Compose installed
2. Built the OpenClaw image with self-deployment support
3. A running OpenClaw instance

## Building the Image

Build the enhanced OpenClaw image with self-deployment capabilities:

```bash
# From the project root
docker compose build --no-cache
```

This builds an image that includes:
- Python 3 and pip
- openclaw-deploy CLI tool
- openclaw-self-deploy script
- Docker CLI (for Docker-in-Docker)

## Test 1: Basic Self-Deployment from Container Shell

This test verifies the self-deployment script works from within the OpenClaw container.

```bash
# Start OpenClaw
docker compose up -d

# Wait for it to be healthy
docker compose ps

# Open a shell in the container
docker compose exec openclaw-gateway bash

# Inside the container, run the self-deploy script
openclaw-self-deploy --help

# Deploy a new instance
openclaw-self-deploy \
  --gateway-port 18790 \
  --no-interactive

# Exit the container
exit
```

**Expected Result:**
- A new OpenClaw deployment should be created in `/tmp/openclaw-deploy`
- The new instance should be accessible at `http://localhost:18790`
- Both instances (original on 18789, new on 18790) should run simultaneously

**Verification:**
```bash
# Check running containers
docker ps | grep openclaw

# Should see both openclaw-gateway containers
```

## Test 2: Self-Deployment with Custom Parameters

Test deployment with specific configuration:

```bash
docker compose exec openclaw-gateway bash

openclaw-self-deploy \
  --target-dir /tmp/my-openclaw \
  --api-key "sk-ant-your-key-here" \
  --gateway-token "my-secure-token" \
  --gateway-port 19000 \
  --no-interactive

exit
```

**Expected Result:**
- Deployment created at `/tmp/my-openclaw`
- Gateway accessible at `http://localhost:19000?token=my-secure-token`
- API key pre-configured in `.env`

**Verification:**
```bash
# Check the deployment
docker exec openclaw-gateway cat /tmp/my-openclaw/.env | grep ANTHROPIC_API_KEY

# Check if container is running
docker ps -f name=openclaw-gateway
```

## Test 3: Docker-in-Docker Permissions

Verify Docker socket access works correctly:

```bash
# Check if container can access Docker
docker compose exec openclaw-gateway docker info

# Should display Docker system information
# If it fails, check docker-compose.yml has Docker socket mounted
```

## Test 4: API Endpoint Integration (Optional)

If you've integrated the API endpoint example:

```bash
# Deploy via API
curl -X POST http://localhost:18789/api/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "apiKey": "sk-ant-xxx",
    "gatewayPort": "18791"
  }'

# Check status
curl http://localhost:18789/api/deploy/status?targetDir=/tmp/openclaw-deploy
```

**Expected Result:**
- API returns JSON response with deployment status
- New instance is deployed and running

## Test 5: Recursive Self-Deployment

Test that the newly deployed OpenClaw instance can also deploy another instance:

```bash
# First deployment
docker compose exec openclaw-gateway bash -c "openclaw-self-deploy --gateway-port 18790 --no-interactive"

# Wait for deployment to complete, then deploy from the new instance
# Note: This requires accessing the new container by name
NEW_CONTAINER=$(docker ps -f name=openclaw-gateway --format "{{.Names}}" | grep -v "^openclaw-gateway$" | head -1)

docker exec $NEW_CONTAINER openclaw-self-deploy --gateway-port 18791 --no-interactive
```

**Expected Result:**
- Three levels of deployment:
  1. Original (port 18789)
  2. First child (port 18790)
  3. Second child (port 18791)

## Test 6: Error Handling

Test that deployment handles errors gracefully:

```bash
# Test with invalid port
docker compose exec openclaw-gateway openclaw-self-deploy --gateway-port invalid

# Test with port already in use
docker compose exec openclaw-gateway openclaw-self-deploy --gateway-port 18789

# Test without Docker access (remove socket mount first)
# Edit docker-compose.yml, comment out Docker socket, restart, then try
```

**Expected Result:**
- Clear error messages
- No partial deployments
- Rollback occurs if deployment fails

## Test 7: Cleanup Testing

Verify cleanup works:

```bash
# From within container or host
openclaw-deploy --project-dir /tmp/openclaw-deploy cleanup --all --no-interactive

# Verify removal
docker ps -a | grep openclaw
ls /tmp/openclaw-deploy  # Should not exist or be cleaned
```

## Common Issues and Solutions

### Issue: "Cannot access Docker daemon"

**Solution:**
Ensure docker-compose.yml has the Docker socket mounted:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Issue: "openclaw-deploy: command not found"

**Solution:**
Rebuild the image to include the tool:
```bash
docker compose build --no-cache
docker compose up -d
```

### Issue: "Permission denied" when accessing Docker

**Solution:**
The container needs access to the Docker socket. Check:
1. Socket is mounted in docker-compose.yml
2. Socket permissions on host: `ls -la /var/run/docker.sock`
3. User in container can read the socket

### Issue: Port conflict

**Solution:**
Use a different port for the new instance:
```bash
openclaw-self-deploy --gateway-port 18800
```

### Issue: Build fails with pip errors

**Solution:**
The Dockerfile uses `--break-system-packages` flag. Ensure you're using Python 3.11+
or remove the flag and use a virtual environment.

## Performance Testing

Measure deployment time:

```bash
time docker compose exec openclaw-gateway openclaw-self-deploy \
  --gateway-port 18790 \
  --no-interactive
```

Typical deployment should complete in 2-5 minutes depending on:
- Network speed (cloning repository)
- Docker build cache
- System resources

## Security Testing

### Test 1: Unauthorized Access Prevention

If API endpoint is integrated, test authentication:

```bash
# Should fail without proper auth
curl -X POST http://localhost:18789/api/deploy \
  -H "Content-Type: application/json" \
  -d '{"gatewayPort": "18790"}'
```

### Test 2: Input Validation

Test with malicious inputs:

```bash
# Command injection attempt
openclaw-self-deploy --gateway-port "8080; rm -rf /"

# Should be safely handled
```

## Load Testing

Test multiple concurrent deployments:

```bash
# Deploy 3 instances simultaneously
for port in 18790 18791 18792; do
    docker compose exec openclaw-gateway openclaw-self-deploy \
      --gateway-port $port \
      --target-dir /tmp/openclaw-$port \
      --no-interactive &
done
wait

# Verify all succeeded
docker ps | grep openclaw | wc -l  # Should show 4 (original + 3 new)
```

## Cleanup After Testing

Remove all test deployments:

```bash
# Stop and remove all openclaw containers
docker ps -a -f name=openclaw | awk '{if(NR>1) print $1}' | xargs docker stop
docker ps -a -f name=openclaw | awk '{if(NR>1) print $1}' | xargs docker rm

# Clean up deployment directories
rm -rf /tmp/openclaw-deploy /tmp/openclaw-* /tmp/my-openclaw

# Remove volumes (optional)
docker volume rm openclaw-home
```

## Automated Testing

For CI/CD, create an automated test script:

```bash
#!/bin/bash
# tests/test-self-deployment.sh

set -e

echo "Building image..."
docker compose build --no-cache

echo "Starting OpenClaw..."
docker compose up -d

echo "Waiting for healthy status..."
timeout 120 bash -c 'until docker compose ps openclaw-gateway | grep -q "healthy"; do sleep 2; done'

echo "Testing self-deployment..."
docker compose exec -T openclaw-gateway openclaw-self-deploy \
  --gateway-port 18790 \
  --no-interactive

echo "Verifying new deployment..."
timeout 120 bash -c 'until curl -sf http://localhost:18790/health; do sleep 2; done'

echo "✓ All tests passed!"

echo "Cleaning up..."
docker compose down -v
```

## Next Steps

After successful testing:

1. Document your deployment use cases
2. Set up monitoring for deployed instances
3. Implement backup/restore procedures
4. Configure production security settings
5. Set up logging aggregation for multiple instances
