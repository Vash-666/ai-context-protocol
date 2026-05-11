/**
 * Async Sessions Spawn Wrapper
 * Wraps OpenClaw's sessions_spawn with async capabilities
 * 
 * @module sessions-spawn-async
 * @version 1.0.0
 * @author Switch (@switch)
 * @date 2026-05-11
 */

const fs = require('fs').promises;
const { asyncSpawn, completeSpawn, registry } = require('./async-spawn');

/**
 * Enhanced sessions_spawn with async support
 * 
 * This function wraps the native sessions_spawn tool to add non-blocking
 * async capabilities while maintaining full backward compatibility.
 * 
 * @param {Object} options - Spawn options
 * @param {string} options.agentId - Target agent ID
 * @param {string} options.task - Task description/context
 * @param {boolean} [options.async=false] - Enable async mode (non-blocking)
 * @param {number} [options.timeout=300000] - Timeout in milliseconds (5 min default)
 * @param {string} [options.onComplete] - Callback channel or file path
 * @param {string} [options.context='isolated'] - Subagent context mode
 * @param {string} [options.model] - Model override for subagent
 * @returns {Promise<Object|SpawnFuture>} Result (sync) or Future (async)
 * 
 * @example
 * // Synchronous mode (existing behavior - blocks until completion)
 * const result = await sessionsSpawnAsync({
 *   agentId: 'quality',
 *   task: 'Audit this code'
 * });
 * 
 * @example
 * // Asynchronous mode (new - returns immediately)
 * const future = await sessionsSpawnAsync({
 *   agentId: 'quality',
 *   task: 'Audit this code',
 *   async: true
 * });
 * 
 * // Do other work...
 * await doOtherWork();
 * 
 * // Retrieve result when needed
 * const result = await future.getResult();
 */
async function sessionsSpawnAsync(options) {
  // Validate options
  if (!options.agentId) {
    throw new Error('agentId is required');
  }
  if (!options.task) {
    throw new Error('task is required');
  }
  
  // If not async mode, use native sessions_spawn (blocking)
  if (!options.async) {
    console.log(`[SessionsSpawn] Sync mode: ${options.agentId}`);
    return nativeSessionsSpawn(options);
  }
  
  // Async mode - integrated with OpenClaw
  console.log(`[SessionsSpawn] Async mode: ${options.agentId}`);
  return asyncSessionsSpawn(options);
}

/**
 * Native sessions_spawn (blocking)
 * Calls the actual OpenClaw sessions_spawn tool
 */
async function nativeSessionsSpawn(options) {
  console.log(`[NativeSpawn] Spawning ${options.agentId}...`);
  
  // Call actual OpenClaw sessions_spawn
  const result = await sessions_spawn({
    agentId: options.agentId,
    task: options.task,
    mode: options.mode || 'run',
    timeoutSeconds: Math.floor((options.timeout || 300000) / 1000),
    model: options.model,
    context: options.context || 'isolated'
  });
  
  return {
    status: 'completed',
    agentId: options.agentId,
    result: result,
    spawnId: result?.runId || 'unknown'
  };
}

/**
 * Async spawn using OpenClaw's native sessions_spawn
 * Spawns subagent without blocking, returns future immediately
 */
async function asyncSessionsSpawn(options) {
  const spawnId = `async-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  console.log(`[AsyncSpawn] Starting async spawn: ${spawnId}`);
  
  // Register in async registry
  const future = await asyncSpawn({
    agentId: options.agentId,
    task: options.task,
    timeout: options.timeout,
    onComplete: options.onComplete,
    spawnId: spawnId
  });
  
  // Store spawn metadata for completion handling
  const spawnMeta = {
    spawnId: spawnId,
    agentId: options.agentId,
    task: options.task,
    startedAt: Date.now(),
    status: 'running'
  };
  
  // Save metadata to file for completion handler
  const metaPath = `/Users/rohitvashist/.openclaw/workspace/.async-spawn/${spawnId}.meta.json`;
  await fs.mkdir('/Users/rohitvashist/.openclaw/workspace/.async-spawn', { recursive: true })
    .catch(() => {});
  await fs.writeFile(metaPath, JSON.stringify(spawnMeta, null, 2)).catch(() => {});
  
  // Start the actual spawn in background (fire-and-forget)
  // The completion will be handled by the subagent announce system
  sessions_spawn({
    agentId: options.agentId,
    task: `[ASYNC-SPAWN] ${options.task}\n\nSpawnID: ${spawnId}\nParent: Switch\nStarted: ${new Date().toISOString()}`,
    mode: 'run',
    timeoutSeconds: Math.floor((options.timeout || 300000) / 1000),
    model: options.model,
    context: options.context || 'isolated'
  }).then(result => {
    // This won't execute in async mode - completion handled by event
    console.log(`[AsyncSpawn] Sync completion (unexpected): ${spawnId}`);
  }).catch(err => {
    console.error(`[AsyncSpawn] Spawn error: ${spawnId}`, err.message);
    registry.fail(spawnId, err);
  });
  
  return future;
}

/**
 * Simulate delay for testing
 */
function simulateDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Handle subagent completion event
 * Called by OpenClaw when a subagent completes (via inter-session message)
 * 
 * @param {Object} event - Completion event from subagent
 * @param {string} event.sessionKey - Subagent session key
 * @param {Object} event.result - Subagent result
 * @param {string} event.runId - Run identifier
 * @param {number} event.tokensUsed - Token usage
 */
async function handleSubagentCompletion(event) {
  const { sessionKey, result, runId, tokensUsed } = event;
  
  // Check if this is an async spawn by looking for ASYNC-SPAWN marker in task
  const isAsyncSpawn = result?.task?.includes('[ASYNC-SPAWN]') || 
                       result?.message?.includes('SpawnID:');
  
  if (isAsyncSpawn) {
    // Extract spawn ID from the task/message
    const spawnIdMatch = (result?.task || result?.message || '').match(/SpawnID:\s*(async-[a-z0-9-]+)/);
    const spawnId = spawnIdMatch ? spawnIdMatch[1] : null;
    
    if (spawnId) {
      console.log(`[SessionsSpawn] Completing async spawn: ${spawnId}`);
      
      // Format result
      const formattedResult = {
        status: 'completed',
        sessionKey: sessionKey,
        runId: runId,
        result: result,
        tokensUsed: tokensUsed || 0,
        completedAt: new Date().toISOString()
      };
      
      // Complete the spawn
      await completeSpawn(spawnId, formattedResult);
      
      // Clean up metadata file
      const metaPath = `/Users/rohitvashist/.openclaw/workspace/.async-spawn/${spawnId}.meta.json`;
      await fs.unlink(metaPath).catch(() => {});
      
      // Notify parent if callback specified
      const record = registry.promises.get(spawnId);
      if (record?.metadata?.onComplete) {
        await notifyCompletion(record.metadata.onComplete, formattedResult);
      }
    }
  } else {
    console.log(`[SessionsSpawn] Sync spawn completed: ${sessionKey}`);
  }
}

/**
 * Notify completion via callback
 * @param {string} callback - Callback channel (telegram, file, webhook)
 * @param {Object} result - Completion result
 */
async function notifyCompletion(callback, result) {
  if (callback.startsWith('file:')) {
    const filepath = callback.replace('file:', '');
    await fs.writeFile(filepath, JSON.stringify(result, null, 2));
    console.log(`[SessionsSpawn] Result written to: ${filepath}`);
  } else if (callback.startsWith('telegram:')) {
    // Telegram notification would be implemented here
    console.log(`[SessionsSpawn] Telegram notification: ${callback}`);
  }
}

/**
 * Extract spawn ID from session key
 * Legacy method - now handled in completion event
 */
function extractSpawnIdFromSession(sessionKey) {
  return null;
}

/**
 * Get status of all async spawns
 * @returns {Array<Object>} Spawn statuses
 */
function getAsyncSpawnStatus() {
  return registry.getAllStatuses();
}

/**
 * Get count of active async spawns
 * @returns {number} Active spawn count
 */
function getActiveAsyncCount() {
  return registry.getActiveCount();
}

/**
 * Wait for multiple async spawns to complete
 * @param {Array<SpawnFuture>} futures - Array of futures
 * @param {Object} options - Wait options
 * @param {number} [options.timeout] - Max wait time
 * @param {boolean} [options.all=true] - Wait for all (true) or any (false)
 * @returns {Promise<Array<Object>>} Results
 */
async function waitForSpawns(futures, options = {}) {
  const { timeout = 300000, all = true } = options;
  
  if (all) {
    // Wait for all to complete
    return Promise.all(
      futures.map(f => f.getResult(timeout))
    );
  } else {
    // Wait for any to complete
    return Promise.race(
      futures.map(f => f.getResult(timeout).then(result => ({ result, future: f })))
    );
  }
}

/**
 * Batch spawn multiple subagents
 * @param {Array<Object>} spawnConfigs - Array of spawn configurations
 * @param {boolean} [async=true] - Use async mode
 * @returns {Promise<Array<SpawnFuture|Object>>} Futures or results
 */
async function batchSpawn(spawnConfigs, async = true) {
  const spawns = spawnConfigs.map(config => ({
    ...config,
    async
  }));
  
  if (async) {
    // Return futures immediately
    return Promise.all(spawns.map(sessionsSpawnAsync));
  } else {
    // Sequential execution (blocking)
    const results = [];
    for (const config of spawns) {
      results.push(await sessionsSpawnAsync(config));
    }
    return results;
  }
}

// Export API
module.exports = {
  sessionsSpawnAsync,
  handleSubagentCompletion,
  getAsyncSpawnStatus,
  getActiveAsyncCount,
  waitForSpawns,
  batchSpawn
};

// CLI demo
if (require.main === module) {
  console.log('Sessions Spawn Async Module - P0-ARC-001');
  console.log('');
  console.log('Demo: Async Spawn');
  console.log('=================');
  
  (async () => {
    // Example 1: Sync spawn (blocking)
    console.log('\n1. Sync spawn (blocking):');
    const syncResult = await sessionsSpawnAsync({
      agentId: 'quality',
      task: 'Analyze code sync'
    });
    console.log('Sync result:', syncResult.status);
    
    // Example 2: Async spawn (non-blocking)
    console.log('\n2. Async spawn (non-blocking):');
    const future = await sessionsSpawnAsync({
      agentId: 'quality',
      task: 'Analyze code async',
      async: true
    });
    console.log('Future created:', future.spawnId);
    console.log('Active spawns:', getActiveAsyncCount());
    
    // Example 3: Batch spawn
    console.log('\n3. Batch async spawn:');
    const futures = await batchSpawn([
      { agentId: 'quality', task: 'Task 1' },
      { agentId: 'content', task: 'Task 2' },
      { agentId: 'product', task: 'Task 3' }
    ], true);
    console.log('Batch created:', futures.length, 'futures');
    console.log('Active spawns:', getActiveAsyncCount());
    
    console.log('\n--- Demo Complete ---');
  })();
}
