/**
 * OpenClaw Self-Deployment API Endpoint Example
 *
 * This is an example of how to add a self-deployment API endpoint to OpenClaw.
 * This code is meant to be integrated into OpenClaw's server/API layer.
 *
 * IMPORTANT: This is an EXAMPLE only. You'll need to adapt this to your
 * specific OpenClaw installation and follow OpenClaw's plugin/extension patterns.
 *
 * Usage in OpenClaw:
 * 1. Add this as a custom route/endpoint in your OpenClaw server
 * 2. Ensure proper authentication/authorization is in place
 * 3. Call via POST /api/deploy with appropriate parameters
 *
 * Security Considerations:
 * - Always require authentication before allowing deployment
 * - Validate all input parameters
 * - Rate limit deployment requests
 * - Log all deployment attempts
 * - Consider requiring admin privileges
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

/**
 * Self-deployment endpoint handler
 *
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 *
 * Request body parameters:
 * - apiKey: Anthropic API key for the new instance (optional)
 * - gatewayToken: Gateway token for the new instance (optional)
 * - gatewayPort: Port for the new instance (default: 18790)
 * - targetDir: Deployment directory (default: /tmp/openclaw-deploy)
 * - interactive: Whether to run interactively (default: false)
 */
async function handleSelfDeploy(req, res) {
    // SECURITY: Add authentication check here
    // if (!req.user || !req.user.isAdmin) {
    //     return res.status(403).json({ error: 'Forbidden: Admin access required' });
    // }

    const {
        apiKey,
        gatewayToken,
        gatewayPort = '18790',
        targetDir = '/tmp/openclaw-deploy',
        interactive = false
    } = req.body;

    // Validate inputs
    if (gatewayPort && !/^\d+$/.test(gatewayPort)) {
        return res.status(400).json({ error: 'Invalid gateway port' });
    }

    // Build command
    const args = [];

    if (targetDir) {
        args.push(`--target-dir "${targetDir}"`);
    }

    if (apiKey) {
        args.push(`--api-key "${apiKey}"`);
    }

    if (gatewayToken) {
        args.push(`--gateway-token "${gatewayToken}"`);
    }

    if (gatewayPort) {
        args.push(`--gateway-port "${gatewayPort}"`);
    }

    if (!interactive) {
        args.push('--no-interactive');
    }

    const command = `openclaw-self-deploy ${args.join(' ')}`;

    try {
        // Log deployment attempt
        console.log(`[Self-Deploy] Starting deployment with command: ${command}`);

        // Execute deployment (this will take time)
        const { stdout, stderr } = await execAsync(command, {
            maxBuffer: 1024 * 1024 * 10, // 10MB buffer for output
            timeout: 600000 // 10 minute timeout
        });

        // Log success
        console.log('[Self-Deploy] Deployment successful');
        console.log('[Self-Deploy] STDOUT:', stdout);

        if (stderr) {
            console.warn('[Self-Deploy] STDERR:', stderr);
        }

        // Return success response
        return res.status(200).json({
            success: true,
            message: 'Deployment completed successfully',
            output: stdout,
            deploymentInfo: {
                targetDir,
                gatewayPort,
                gatewayUrl: `http://localhost:${gatewayPort}`
            }
        });

    } catch (error) {
        // Log failure
        console.error('[Self-Deploy] Deployment failed:', error);

        return res.status(500).json({
            success: false,
            error: 'Deployment failed',
            message: error.message,
            stdout: error.stdout || '',
            stderr: error.stderr || ''
        });
    }
}

/**
 * Get deployment status endpoint handler
 *
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
async function handleDeploymentStatus(req, res) {
    const { targetDir = '/tmp/openclaw-deploy' } = req.query;

    try {
        const command = `openclaw-deploy --project-dir "${targetDir}" status`;
        const { stdout } = await execAsync(command);

        return res.status(200).json({
            success: true,
            status: stdout
        });

    } catch (error) {
        return res.status(500).json({
            success: false,
            error: 'Failed to get deployment status',
            message: error.message
        });
    }
}

/**
 * Example Express.js route setup
 *
 * Add these routes to your OpenClaw server
 */
function setupSelfDeploymentRoutes(app) {
    // POST /api/deploy - Trigger self-deployment
    app.post('/api/deploy', handleSelfDeploy);

    // GET /api/deploy/status - Get deployment status
    app.get('/api/deploy/status', handleDeploymentStatus);
}

// Export for use in OpenClaw
module.exports = {
    handleSelfDeploy,
    handleDeploymentStatus,
    setupSelfDeploymentRoutes
};

/**
 * Example usage in OpenClaw:
 *
 * const { setupSelfDeploymentRoutes } = require('./integration-examples/api-endpoint');
 * setupSelfDeploymentRoutes(app);
 *
 * Then make requests:
 *
 * curl -X POST http://localhost:18789/api/deploy \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "apiKey": "sk-ant-xxx",
 *     "gatewayPort": "18790"
 *   }'
 *
 * curl http://localhost:18789/api/deploy/status?targetDir=/tmp/openclaw-deploy
 */
