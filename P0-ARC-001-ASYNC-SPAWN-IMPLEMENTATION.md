# P0-ARC-001: Async Spawn Refactor — Implementation Plan

**Date:** 2026-05-11  
**Status:** 🔄 IN PROGRESS  
**Agent:** @switch (with @quality, @product, @content analysis)

---

## Executive Summary

This document implements P0-ARC-001 (Async Spawn Refactor) based on comprehensive multi-agent analysis. The solution works within OpenClaw's existing architecture while enabling true non-blocking subagent spawning.

---

## 1. Problem Statement (from @quality Analysis)

### Current Blocking Behavior
```
Parent Agent          sessions_spawn          Subagent
    │                       │                    │
    │──────────────────────▶│                    │
    │                       │───────────────────▶│
    │                       │                    │
    │◀──────────────────────│◀───────────────────│
    │    (BLOCKED HERE)     │   (working...)     │
    │                       │                    │
```

**Blocking Point:** `sessions_yield` pauses parent until completion event arrives.

### Costs of Blocking
| Metric | Impact |
|--------|--------|
| **Token Overhead** | Double context (parent + child) |
| **Parent Productivity** | Zero during subagent execution |
| **Latency** | Sequential execution only |
| **Resource Utilization** | Parent session held but idle |

---

## 2. Solution Architecture

### 2.1 Design Principles (from @content Research)

| Principle | Source | Application |
|-----------|--------|-------------|
| **Event-Driven** | Kubernetes Controller | Push-based completion, no polling |
| **Promise/Future** | RQ/Celery | Return handle immediately, await later |
| **State in Sessions** | OpenAI Agents SDK | Sessions as source of truth |
| **Fail Fast** | Circuit Breaker | Timeout and recovery patterns |

### 2.2 Async Spawn Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Parent Agent   │────▶│  sessions_spawn  │────▶│  Subagent       │
│  (@switch)      │     │  (async mode)    │     │  (new session)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                          │
         │◀────SpawnFuture───────│                          │
         │  (immediate return)   │                          │
         │                       │                          │
         ▼                       │                          ▼
┌─────────────────┐             │                ┌─────────────────┐
│ Continue Work   │             │                │ Execute Task    │
│ (don't block)   │             │                │                 │
└─────────────────┘             │                └─────────────────┘
         │                       │                          │
         │                       │◀────Completion Event─────│
         │                       │                          │
         │◀────Result Available──│                          │
         │   (via callback/file) │                          │
         ▼                       ▼                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Retrieve Result │     │  Update Registry │     │  Subagent       │
│ (when needed)   │     │  (mark complete) │     │  (completed)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## 3. Implementation Components

### 3.1 Core Components (from @product Design)

| Component | Responsibility | Status |
|-----------|---------------|--------|
| **SpawnManager** | Handle async spawn requests | 🔄 Implementing |
| **PromiseRegistry** | Track pending subagents | 🔄 Implementing |
| **TokenTracker** | Reserve/reconcile tokens | 📋 Planned |
| **LimitEnforcer** | Maintain spawn limits | ✅ Existing |
| **EventEmitter** | Push completion events | 🔄 Implementing |
| **ResultStore** | Persist subagent results | 🔄 Implementing |

### 3.2 API Design

```typescript
// New async spawn interface
interface AsyncSpawnOptions {
  task: string;
  agentId: string;
  async: true;              // Enable non-blocking mode
  timeout?: number;         // Max execution time (ms)
  onComplete?: string;      // Callback channel/file
  priority?: 'high' | 'normal' | 'low';
}

interface SpawnFuture {
  id: string;               // Unique spawn ID
  sessionKey: string;       // Subagent session key
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  estimatedTokens: number;  // For budget tracking
}

// Usage
const future = await sessions_spawn({
  agentId: 'quality',
  task: 'Analyze code',
  async: true,
  timeout: 300000,          // 5 minutes
  onComplete: 'file:results.json'
});

// Parent continues immediately...
await doOtherWork();

// Later: retrieve result
const result = await future.getResult();
```

---

## 4. Implementation Phases

### Phase 1: Foundation (This Sprint)
- [ ] Create PromiseRegistry for tracking async spawns
- [ ] Implement ResultStore (file-based persistence)
- [ ] Add async mode to sessions_spawn
- [ ] Create spawn completion event emitter

### Phase 2: Token Tracking (Next Sprint)
- [ ] Implement token reservation on async spawn
- [ ] Add cross-boundary token aggregation
- [ ] Create budget reconciliation on completion
- [ ] Add cost alerts at thresholds

### Phase 3: Observability (Future)
- [ ] Spawn tree visualization
- [ ] Distributed tracing
- [ ] Performance metrics dashboard
- [ ] Historical trend analysis

### Phase 4: Advanced Features (Future)
- [ ] Queue-based backpressure
- [ ] Priority scheduling
- [ ] Batch spawn operations
- [ ] Circuit breaker for failures

---

## 5. Risk Mitigation

| Risk | Mitigation | Status |
|------|-----------|--------|
| **Orphaned Spawns** | Parent heartbeat + 60s timeout cleanup | 📋 Planned |
| **Token Overflow** | Conservative 120% reservation + reconciliation | 📋 Planned |
| **Memory Leaks** | Promise registry with 1-hour TTL | 📋 Planned |
| **Race Conditions** | Atomic state transitions | 📋 Planned |
| **Backward Compatibility** | Async mode opt-in only | ✅ Implemented |

---

## 6. Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `lib/async-spawn.js` | Core async spawn implementation |
| `lib/promise-registry.js` | Track pending subagents |
| `lib/result-store.js` | Persist subagent results |
| `lib/token-tracker.js` | Async token budget management |

### Modified Files
| File | Change |
|------|--------|
| `tools/sessions_spawn.js` | Add async mode support |
| `AGENTS.md` | Document async spawn patterns |
| `P0-ARC-001-IMPLEMENTATION.md` | This document |

---

## 7. Success Criteria

- [ ] Parent can spawn subagent without blocking
- [ ] Parent can do other work while subagent runs
- [ ] Results are retrievable after completion
- [ ] Token usage tracked across async boundaries
- [ ] Existing spawn limits still enforced
- [ ] Backward compatible (sync mode still works)

---

## 8. Multi-Agent Analysis Summary

### @quality Findings
- Blocking occurs at `sessions_yield`
- Double token cost during wait
- Parent context held but idle

### @product Design
- Promise/Future pattern for async results
- Event-driven completion delivery
- 6 core components with 4-phase rollout

### @content Research
- Kubernetes Controller pattern for reconciliation
- OpenAI Agents SDK for session management
- RQ/Celery patterns for task queues

---

**Next Step:** Begin Phase 1 implementation with PromiseRegistry and ResultStore.
