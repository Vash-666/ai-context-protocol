# SYSTEM BACKLOG

> **Last Updated:** 2026-05-08
> **Audit Source:** Grok (xAI) System Audit
> **Overall Severity:** 9.4/10

---

## P0 - FIX TODAY (Critical Showstoppers)

| # | Issue | Severity | Description | Fix | Owner | Status |
|---|-------|----------|-------------|-----|-------|--------|
| 1 | **Gemini API Key Expired** | 10/10 | ~~"Complete showstopper"~~ **MISDIAGNOSED**: Key is valid. Real issue: embedding model misconfigured. | ✅ Config fixed: Now using `gemini-embedding-001` in openclaw.json | @switch | ✅ FIXED (requires OpenClaw restart) |
| 2 | **Health Scripts Unscheduled** | 10/10 | "Code exists but not in cron." Health monitoring exists but isn't running automatically. | Add health scripts to crontab with appropriate intervals (every 5 min for critical, hourly for full) | @scaffolder | 🔴 NOT STARTED |
| 3 | **Inline Spawn Protocol** | 10/10 | "Synchronous, blocks parent." Partially mitigated: @scaffolder runs independently, but @switch still waits. | ✅ Mitigated via independent subagent execution; full async requires architectural refactor | @switch | 🟡 MITIGATED |

### P0 Sprint Breakdown

#### Sprint 1: Emergency API Key (4 hours)
**Goal:** Restore Gemini API functionality
- [ ] Generate new API key at https://aistudio.google.com/app/apikey
- [ ] Update key in environment/config files
- [ ] Test memory search functionality
- [ ] Document key rotation procedure

**Acceptance Criteria:**
- `memory_search` tool returns valid results
- No "API key expired" errors in logs
- Key stored securely (not in plaintext if possible)

**Handoff:** @switch → Verify with test memory query

---

#### Sprint 2: Cron Scheduling (2 hours)
**Goal:** Automate health monitoring
- [ ] Identify all health scripts in codebase
- [ ] Create crontab entries with proper intervals
- [ ] Add logging to health script outputs
- [ ] Test cron execution manually

**Acceptance Criteria:**
- `crontab -l` shows health script entries
- Health logs appear in expected location
- Scripts run without manual intervention

**Handoff:** @scaffolder → Verify logs after 1 hour

---

#### Sprint 3: Async Spawn Refactor (1-2 days)
**Goal:** Fix blocking spawn architecture
- [ ] Audit all spawn calls in codebase
- [ ] Implement async spawn wrapper
- [ ] Add completion callbacks/promises
- [ ] Update documentation

**Acceptance Criteria:**
- Parent agent doesn't block on spawn
- Spawn results propagate correctly
- No regression in spawn functionality

**Handoff:** @switch → Code review required

---

## P1 - FIX THIS WEEK (High Priority)

| # | Issue | Severity | Description | Fix | Owner | Status |
|---|-------|----------|-------------|-----|-------|--------|
| 4 | **Expired Keys in Configs** | 8/10 | Multiple expired API keys scattered in configs, no rotation policy. | Audit all configs → Remove expired keys → Implement key rotation schedule | @scaffolder | 🔴 NOT STARTED |
| 5 | **No Spawn Limits** | 8/10 | "Infinite agent tree risk." No protection against runaway agent spawning. | Add max depth counter → Implement spawn quota per session → Add circuit breaker | @switch | 🔴 NOT STARTED |
| 6 | **No Tool Permission Boundaries** | 8/10 | Agents share tool access without permission isolation. | Design permission matrix → Implement tool access controls → Add audit logging | @switch | 🔴 NOT STARTED |
| 7 | **Smart Router v2 Latency** | 7/10 | "Inline routing" causes performance issues. | Profile routing code → Implement caching → Consider async routing | @switch | 🔴 NOT STARTED |
| 8 | **Zero Observability** | 7/10 | "No token tracking, latency metrics." Flying blind on performance. | Add OpenTelemetry or similar → Track token usage per request → Log latency metrics | @scaffolder | 🔴 NOT STARTED |
| 9 | **Sequential Execution** | 7/10 | "Forces blocking" - no parallel processing. | Identify parallelizable operations → Implement worker pool → Add async/await patterns | @switch | 🔴 NOT STARTED |

### P1 Sprint Suggestions

**Sprint 4: Security Hardening (2-3 days)**
- Items: #4, #5, #6
- Focus: Key rotation + spawn limits + permissions

**Sprint 5: Observability Stack (2 days)**
- Items: #8
- Focus: Metrics collection and dashboard

**Sprint 6: Performance Optimization (3 days)**
- Items: #7, #9
- Focus: Router optimization and parallelization

---

## P2 - FIX THIS MONTH (Architecture Debt)

| # | Issue | Severity | Description | Fix | Owner | Status |
|---|-------|----------|-------------|-----|-------|--------|
| 10 | **Health Scripts Not Scheduled** | 9.5/10 | Duplicate of #2, but noted as missing automation. | (See Sprint 2) | @scaffolder | 🔴 NOT STARTED |
| 11 | **No API Key Expiration Monitoring** | 9.5/10 | No proactive alerts before keys expire. | Build key expiration checker → Add alerting (email/Slack) → Schedule daily checks | @scaffolder | 🔴 NOT STARTED |
| 12 | **No Automated Testing** | 9.5/10 | "Despite @quality agent" - tests exist but don't run automatically. | Set up CI pipeline → Add pre-commit hooks → Schedule test runs | @scaffolder | 🔴 NOT STARTED |
| 13 | **Manual Website Deployment** | 9.5/10 | Deployment requires manual steps. | Create deployment script → Add GitHub Actions → Document rollback procedure | @scaffolder | 🔴 NOT STARTED |
| 14 | **No Agent Lifecycle Management** | 9.5/10 | Agents spawn but aren't tracked or cleaned up. | Build agent registry → Add health checks → Implement auto-termination | @switch | 🔴 NOT STARTED |
| 15 | **"Cosplay Multi-Agent"** | 8/10 | "Names but no orchestration" - agents exist but don't coordinate. | Design orchestration protocol → Implement message bus → Add agent discovery | @switch | 🔴 NOT STARTED |
| 16 | **No Resilience Patterns** | 8/10 | "No circuit breakers, fallbacks" - fragile failure handling. | Implement circuit breaker pattern → Add retry logic with backoff → Design fallback chains | @switch | 🔴 NOT STARTED |
| 17 | **Smart Router v1 Disaster** | 8/10 | "Smart Router v2 implies v1 disaster" - legacy router issues. | Audit v1 router usage → Plan migration → Deprecate v1 | @switch | 🔴 NOT STARTED |

### P2 Sprint Suggestions

**Sprint 7: Automation Infrastructure (1 week)**
- Items: #11, #12, #13
- Focus: CI/CD, monitoring, key management

**Sprint 8: Agent Architecture Redesign (2 weeks)**
- Items: #14, #15, #16, #17
- Focus: True multi-agent orchestration

---

## IMMEDIATE ACTION PLAN (Next 30 Minutes)

### Can Fix RIGHT NOW:

1. **Generate New Gemini API Key** (5 min)
   - Go to https://aistudio.google.com/app/apikey
   - Create new key
   - Update in environment/config

2. **Add Health Scripts to Cron** (10 min)
   ```bash
   # Add to crontab
   */5 * * * * /path/to/health-check.sh >> /var/log/openclaw-health.log 2>&1
   0 * * * * /path/to/full-health.sh >> /var/log/openclaw-full.log 2>&1
   ```

3. **Quick Spawn Audit** (15 min)
   - Search codebase for spawn calls
   - Identify blocking patterns
   - Document findings for Sprint 3

### Needs @switch:
- Item #1 (Gemini key verification)
- Item #3 (Async spawn refactor)
- All architecture decisions

### Needs @scaffolder:
- Item #2 (Cron scheduling)
- Items #4, #8, #11, #12, #13 (Infrastructure/DevOps)
- CI/CD setup

### Needs External:
- Google AI Studio access for key generation
- Server access for cron setup
- Possibly new monitoring service (Datadog/NewRelic) for observability

---

## GROK'S ORIGINAL QUOTES (Context)

> "Complete showstopper, memory search dead" - On Gemini API key

> "Code exists but not in cron" - On health scripts

> "Synchronous, blocks parent, architectural malpractice" - On inline spawn

> "Cosplay multi-agent — names but no orchestration" - On agent architecture

> "Smart Router v2 implies v1 disaster" - On router evolution

---

## PROGRESS TRACKING

| Date | Completed | Blocked | Notes |
|------|-----------|---------|-------|
| 2026-05-08 | Backlog created | All items | Initial audit complete |

---

## NEXT REVIEW

**Review Date:** 2026-05-09
**Review Focus:** P0 item completion status
**Owner:** @switch
