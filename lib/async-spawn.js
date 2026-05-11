/**
 * Async Spawn Module - P0-ARC-001 Implementation
 * Enables non-blocking subagent spawning for OpenClaw
 * 
 * @module async-spawn
 * @version 1.0.0
 * @author Switch (@switch)
 * @date 2026-05-11
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

// Configuration
const CONFIG = {
  RESULT_STORE_DIR: process.env.ASYNC_SPAWN_STORE || '/Users/rohitvashist/.openclaw/workspace/.async-spawn',
  DEFAULT_TIMEOUT: 300000, // 5 minutes
  PROMISE_TTL: 3600000,    // 1 hour cleanup
  MAX_CONCURRENT: 8,
  TOKEN_RESERVE_RATIO: 1.2 // 120% of estimate
};

/**
 * PromiseRegistry - Tracks pending async spawns
 */
class PromiseRegistry extends EventEmitter {
  constructor() {
    super();
    this.promises = new Map();
    this.timeouts = new Map();
    
    // Start cleanup interval
    setInterval(() => this.cleanup(), 60000); // Every minute
  }
  
  /**
   * Register a new async spawn
   * @param {string} spawnId - Unique spawn identifier
   * @param {Object} metadata - Spawn metadata
   * @returns {SpawnFuture} Future object for result retrieval
   */
  register(spawnId, metadata) {
    const future = new SpawnFuture(spawnId, metadata);
    this.promises.set(spawnId, {
      future,
      metadata,
      createdAt: Date.now(),
      status: 'pending'
    });
    
    // Set timeout for auto-cleanup
    const timeout = metadata.timeout || CONFIG.DEFAULT_TIMEOUT;
    this.timeouts.set(spawnId, setTimeout(() => {
      this.timeout(spawnId);
    }, timeout));
    
    this.emit('registered', { spawnId, metadata });
    return future;
  }
  
  /**
   * Mark spawn as completed
   * @param {string} spawnId - Spawn identifier
   * @param {Object} result - Subagent result
   */
  complete(spawnId, result) {
    const record = this.promises.get(spawnId);
    if (!record) {
      console.warn(`[AsyncSpawn] Complete called for unknown spawn: ${spawnId}`);
      return;
    }
    
    record.status = 'completed';
    record.completedAt = Date.now();
    record.result = result;
    
    // Clear timeout
    if (this.timeouts.has(spawnId)) {
      clearTimeout(this.timeouts.get(spawnId));
      this.timeouts.delete(spawnId);
    }
    
    // Resolve the future
    record.future._resolve(result);
    
    this.emit('completed', { spawnId, result, duration: record.completedAt - record.createdAt });
  }
  
  /**
   * Mark spawn as failed
   * @param {string} spawnId - Spawn identifier
   * @param {Error} error - Failure reason
   */
  fail(spawnId, error) {
    const record = this.promises.get(spawnId);
    if (!record) {
      console.warn(`[AsyncSpawn] Fail called for unknown spawn: ${spawnId}`);
      return;
    }
    
    record.status = 'failed';
    record.failedAt = Date.now();
    record.error = error;
    
    // Clear timeout
    if (this.timeouts.has(spawnId)) {
      clearTimeout(this.timeouts.get(spawnId));
      this.timeouts.delete(spawnId);
    }
    
    // Reject the future
    record.future._reject(error);
    
    this.emit('failed', { spawnId, error });
  }
  
  /**
   * Handle spawn timeout
   * @param {string} spawnId - Spawn identifier
   */
  timeout(spawnId) {
    const record = this.promises.get(spawnId);
    if (!record || record.status !== 'pending') {
      return;
    }
    
    this.fail(spawnId, new Error(`Spawn ${spawnId} timed out after ${CONFIG.DEFAULT_TIMEOUT}ms`));
  }
  
  /**
   * Get spawn status
   * @param {string} spawnId - Spawn identifier
   * @returns {Object|null} Spawn status or null if not found
   */
  getStatus(spawnId) {
    const record = this.promises.get(spawnId);
    if (!record) return null;
    
    return {
      spawnId,
      status: record.status,
      createdAt: record.createdAt,
      duration: Date.now() - record.createdAt,
      metadata: record.metadata
    };
  }
  
  /**
   * Cleanup expired promises
   */
  cleanup() {
    const now = Date.now();
    let cleaned = 0;
    
    for (const [spawnId, record] of this.promises) {
      const age = now - record.createdAt;
      
      // Clean up completed/failed after TTL
      if ((record.status === 'completed' || record.status === 'failed') && age > CONFIG.PROMISE_TTL) {
        this.promises.delete(spawnId);
        cleaned++;
      }
    }
    
    if (cleaned > 0) {
      console.log(`[AsyncSpawn] Cleaned up ${cleaned} expired promises`);
    }
  }
  
  /**
   * Get active spawn count
   * @returns {number} Number of pending/running spawns
   */
  getActiveCount() {
    return Array.from(this.promises.values()).filter(
      r => r.status === 'pending' || r.status === 'running'
    ).length;
  }
  
  /**
   * Get all spawn statuses
   * @returns {Array<Object>} All spawn statuses
   */
  getAllStatuses() {
    return Array.from(this.promises.keys()).map(id => this.getStatus(id));
  }
}

/**
 * SpawnFuture - Handle for retrieving async spawn results
 */
class SpawnFuture {
  constructor(spawnId, metadata) {
    this.spawnId = spawnId;
    this.metadata = metadata;
    this._resolveFn = null;
    this._rejectFn = null;
    this._promise = new Promise((resolve, reject) => {
      this._resolveFn = resolve;
      this._rejectFn = reject;
    });
  }
  
  /**
   * Get the result (awaits completion)
   * @param {number} timeout - Max wait time in ms
   * @returns {Promise<Object>} Subagent result
   */
  async getResult(timeout = CONFIG.DEFAULT_TIMEOUT) {
    return Promise.race([
      this._promise,
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('GetResult timeout')), timeout)
      )
    ]);
  }
  
  /**
   * Check if result is available (non-blocking)
   * @returns {boolean}
   */
  isReady() {
    // This would need to check the registry
    // Simplified for now
    return false;
  }
  
  /**
   * Internal: Resolve the future
   * @private
   */
  _resolve(result) {
    if (this._resolveFn) {
      this._resolveFn(result);
    }
  }
  
  /**
   * Internal: Reject the future
   * @private
   */
  _reject(error) {
    if (this._rejectFn) {
      this._rejectFn(error);
    }
  }
}

/**
 * ResultStore - Persists subagent results
 */
class ResultStore {
  constructor() {
    this.baseDir = CONFIG.RESULT_STORE_DIR;
    this._ensureDir();
  }
  
  async _ensureDir() {
    try {
      await fs.mkdir(this.baseDir, { recursive: true });
    } catch (err) {
      console.error('[AsyncSpawn] Failed to create result store:', err);
    }
  }
  
  /**
   * Save result to store
   * @param {string} spawnId - Spawn identifier
   * @param {Object} result - Result data
   */
  async save(spawnId, result) {
    const filepath = path.join(this.baseDir, `${spawnId}.json`);
    const data = {
      spawnId,
      savedAt: new Date().toISOString(),
      result
    };
    
    await fs.writeFile(filepath, JSON.stringify(data, null, 2));
    return filepath;
  }
  
  /**
   * Load result from store
   * @param {string} spawnId - Spawn identifier
   * @returns {Object|null} Result data or null
   */
  async load(spawnId) {
    const filepath = path.join(this.baseDir, `${spawnId}.json`);
    
    try {
      const data = await fs.readFile(filepath, 'utf8');
      return JSON.parse(data);
    } catch (err) {
      if (err.code === 'ENOENT') {
        return null;
      }
      throw err;
    }
  }
  
  /**
   * Delete result from store
   * @param {string} spawnId - Spawn identifier
   */
  async delete(spawnId) {
    const filepath = path.join(this.baseDir, `${spawnId}.json`);
    
    try {
      await fs.unlink(filepath);
    } catch (err) {
      if (err.code !== 'ENOENT') {
        throw err;
      }
    }
  }
}

/**
 * TokenTracker - Manages token budgets for async spawns
 */
class TokenTracker {
  constructor() {
    this.reservations = new Map();
    this.usage = new Map();
  }
  
  /**
   * Reserve tokens for async spawn
   * @param {string} spawnId - Spawn identifier
   * @param {number} estimatedTokens - Estimated token usage
   * @returns {number} Reserved amount (120% of estimate)
   */
  reserve(spawnId, estimatedTokens) {
    const reserved = Math.ceil(estimatedTokens * CONFIG.TOKEN_RESERVE_RATIO);
    this.reservations.set(spawnId, {
      reserved,
      estimated: estimatedTokens,
      reservedAt: Date.now()
    });
    return reserved;
  }
  
  /**
   * Record actual token usage
   * @param {string} spawnId - Spawn identifier
   * @param {number} actualTokens - Actual tokens used
   */
  recordUsage(spawnId, actualTokens) {
    this.usage.set(spawnId, {
      actual: actualTokens,
      recordedAt: Date.now()
    });
    
    // Calculate reconciliation
    const reservation = this.reservations.get(spawnId);
    if (reservation) {
      const variance = reservation.reserved - actualTokens;
      return {
        reserved: reservation.reserved,
        actual: actualTokens,
        variance,
        efficiency: actualTokens / reservation.reserved
      };
    }
    
    return null;
  }
  
  /**
   * Get total reserved tokens
   * @returns {number} Sum of all reservations
   */
  getTotalReserved() {
    return Array.from(this.reservations.values()).reduce(
      (sum, r) => sum + r.reserved, 0
    );
  }
  
  /**
   * Get total actual usage
   * @returns {number} Sum of all recorded usage
   */
  getTotalUsage() {
    return Array.from(this.usage.values()).reduce(
      (sum, u) => sum + u.actual, 0
    );
  }
}

// Global instances
const registry = new PromiseRegistry();
const resultStore = new ResultStore();
const tokenTracker = new TokenTracker();

/**
 * Main async spawn function
 * @param {Object} options - Spawn options
 * @param {string} options.task - Task description
 * @param {string} options.agentId - Target agent
 * @param {boolean} options.async - Enable async mode
 * @param {number} options.timeout - Timeout in ms
 * @param {string} options.onComplete - Completion callback
 * @returns {Promise<SpawnFuture>} Future for result retrieval
 */
async function asyncSpawn(options) {
  // Generate unique spawn ID
  const spawnId = `async-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Check concurrent limit
  if (registry.getActiveCount() >= CONFIG.MAX_CONCURRENT) {
    throw new Error(`Max concurrent spawns (${CONFIG.MAX_CONCURRENT}) reached`);
  }
  
  // Estimate tokens (simplified - would use actual estimation)
  const estimatedTokens = options.task ? options.task.length * 2 : 1000;
  const reserved = tokenTracker.reserve(spawnId, estimatedTokens);
  
  // Register the spawn
  const future = registry.register(spawnId, {
    agentId: options.agentId,
    task: options.task,
    timeout: options.timeout,
    onComplete: options.onComplete,
    estimatedTokens,
    reservedTokens: reserved
  });
  
  console.log(`[AsyncSpawn] Spawned ${spawnId} (${options.agentId}) - Reserved ${reserved} tokens`);
  
  // Here we would actually spawn the subagent
  // For now, this is a placeholder for the actual spawn mechanism
  // The real implementation would integrate with OpenClaw's sessions_spawn
  
  return future;
}

/**
 * Complete an async spawn (called by subagent on completion)
 * @param {string} spawnId - Spawn identifier
 * @param {Object} result - Subagent result
 */
async function completeSpawn(spawnId, result) {
  // Save result
  await resultStore.save(spawnId, result);
  
  // Record token usage (would come from actual subagent metrics)
  const reconciliation = tokenTracker.recordUsage(spawnId, result.tokensUsed || 0);
  
  // Complete in registry
  registry.complete(spawnId, result);
  
  console.log(`[AsyncSpawn] Completed ${spawnId}`, reconciliation);
}

// Export module
module.exports = {
  asyncSpawn,
  completeSpawn,
  registry,
  resultStore,
  tokenTracker,
  SpawnFuture,
  PromiseRegistry,
  ResultStore,
  TokenTracker,
  CONFIG
};

// CLI usage example
if (require.main === module) {
  console.log('Async Spawn Module - P0-ARC-001');
  console.log('Usage: const { asyncSpawn } = require("./async-spawn");');
  console.log('');
  console.log('Active spawns:', registry.getActiveCount());
  console.log('Total reserved tokens:', tokenTracker.getTotalReserved());
}
