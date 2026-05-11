/**
 * Async Sessions Spawn Wrapper
 * Wraps OpenClaw's sessions_spawn with async capabilities
 * 
 * @module sessions-spawn-async
 * @version 1.0.0
 * @author Switch (@switch)
 * @date 2026-05-11
 */

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
    
    // This would call the actual OpenClaw sessions_spawn tool
    // For now, we simulate it
    return nativeSessionsSpawn(options);
  }
  
  // Async mode
  console.log(`[SessionsSpawn] Async mode: ${options.agentId}`);
  
  // Create async spawn
  const future = await asyncSpawn({
    agentId: options.agentId,
    task: options.task,
    timeout: options.timeout,
    onComplete: options.onComplete,
    context: options.context,
    model: options.model
  });
  
  // If we have access to the actual OpenClaw spawn mechanism,
  // we would trigger it here and wire up the completion handler
  // For now, this is a framework that integrates with the real system
  
  return future;
}

/**
 * Native sessions_spawn (blocking)
 * This simulates the actual OpenClaw sessions_spawn behavior
 * In production, this would call the real tool
 */
async function nativeSessionsSpawn(options) {
  // Simulate blocking spawn
  console.log(`[NativeSpawn] Spawning ${options.agentId}...`);
  
  // In real implementation, this would be:
  // return await tool('sessions_spawn', options);
  
  // Simulate work
  await simulateDelay(1000);
  
  return {
    status: 'completed',
    agentId: options.agentId,
    result: `Simulated result from ${options.agentId}`,
    tokensUsed: Math.floor(Math.random() * 5000) + 1000
  };
}

/**
 * Simulate delay for testing
 */
function simulateDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Handle subagent completion event
 * This would be called by OpenClaw when a subagent completes
 * 
 * @param {string} sessionKey - Subagent session key
 * @param {Object} result - Subagent result
 */
async function handleSubagentCompletion(sessionKey, result) {
  // Extract spawn ID from session key or metadata
  const spawnId = extractSpawnIdFromSession(sessionKey);
  
  if (spawnId && spawnId.startsWith('async-')) {
    console.log(`[SessionsSpawn] Completing async spawn: ${spawnId}`);
    await completeSpawn(spawnId, result);
  } else {
    console.log(`[SessionsSpawn] Sync spawn completed: ${sessionKey}`);
    // Handle sync completion (normal flow)
  }
}

/**
 * Extract spawn ID from session key
 * In production, this would parse the session metadata
 */
function extractSpawnIdFromSession(sessionKey) {
  // This is a placeholder - real implementation would
  // look up the spawn ID from session metadata
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
