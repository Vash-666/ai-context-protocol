/**
 * Async Spawn Integration for OpenClaw Main Agent
 * 
 * This module integrates async spawn completion handling into the main agent.
 * Add this to the main agent's message handling logic.
 * 
 * @module async-spawn-integration
 * @version 1.0.0
 * @date 2026-05-11
 */

const { handleSubagentCompletion, getAsyncSpawnStatus } = require('./sessions-spawn-async');

/**
 * Process inter-session message for async spawn completion
 * Call this from the main agent's message handler when receiving
 * subagent completion events.
 * 
 * @param {Object} message - Inter-session message
 * @returns {boolean} True if message was handled as async spawn completion
 */
async function processInterSessionMessage(message) {
  // Check if this is a subagent completion event
  const isCompletionEvent = message?.source === 'subagent' && 
                            message?.type === 'subagent task' &&
                            message?.status === 'completed';
  
  if (!isCompletionEvent) {
    return false;
  }
  
  // Check if it's an async spawn by looking at the task content
  const taskContent = message?.result?.task || message?.task || '';
  const isAsyncSpawn = taskContent.includes('[ASYNC-SPAWN]');
  
  if (isAsyncSpawn) {
    console.log('[AsyncIntegration] Processing async spawn completion');
    
    await handleSubagentCompletion({
      sessionKey: message.session_key,
      result: message.result,
      runId: message.run_id,
      tokensUsed: message.stats?.totalTokens
    });
    
    return true;
  }
  
  return false;
}

/**
 * Middleware for agent message processing
 * Wraps the agent's message handler to intercept async spawn completions
 */
function createAsyncSpawnMiddleware(agentMessageHandler) {
  return async function(message, ...args) {
    // Try to handle as async spawn completion first
    const handled = await processInterSessionMessage(message);
    
    if (handled) {
      // Async spawn completion was handled, don't pass to agent
      return { handled: true, type: 'async_spawn_completion' };
    }
    
    // Not an async spawn completion, pass to original handler
    return agentMessageHandler(message, ...args);
  };
}

/**
 * Get dashboard data for async spawns
 * Returns current status of all async spawns for UI display
 */
function getAsyncSpawnDashboard() {
  const statuses = getAsyncSpawnStatus();
  
  return {
    total: statuses.length,
    pending: statuses.filter(s => s.status === 'pending').length,
    running: statuses.filter(s => s.status === 'running').length,
    completed: statuses.filter(s => s.status === 'completed').length,
    failed: statuses.filter(s => s.status === 'failed').length,
    spawns: statuses
  };
}

/**
 * Check if any async spawns are pending
 * Useful for determining if agent should wait or continue
 */
function hasPendingAsyncSpawns() {
  const statuses = getAsyncSpawnStatus();
  return statuses.some(s => s.status === 'pending' || s.status === 'running');
}

/**
 * Wait for all pending async spawns to complete
 * @param {number} timeout - Max wait time in ms
 * @returns {Promise<boolean>} True if all completed, false if timeout
 */
async function waitForAllAsyncSpawns(timeout = 300000) {
  const start = Date.now();
  
  while (hasPendingAsyncSpawns()) {
    if (Date.now() - start > timeout) {
      console.warn('[AsyncIntegration] Timeout waiting for async spawns');
      return false;
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return true;
}

// Export integration API
module.exports = {
  processInterSessionMessage,
  createAsyncSpawnMiddleware,
  getAsyncSpawnDashboard,
  hasPendingAsyncSpawns,
  waitForAllAsyncSpawns
};

// Example usage for main agent
if (require.main === module) {
  console.log('Async Spawn Integration Module');
  console.log('');
  console.log('Usage in main agent:');
  console.log('  const { processInterSessionMessage } = require("./async-spawn-integration");');
  console.log('');
  console.log('  // In message handler:');
  console.log('  const handled = await processInterSessionMessage(message);');
  console.log('  if (handled) return; // Async spawn completion handled');
  console.log('');
  console.log('Dashboard:', getAsyncSpawnDashboard());
}
