╔══════════════════════════════════════════════════════════════════╗
║           OpenClaw Execution Autopsy Report                      ║
╚══════════════════════════════════════════════════════════════════╝

📊 Analyzed 241 events across 183 traces

## Agent Performance

**observability**
  • Events: 91
  • Error rate: 0.0%

**website_builder**
  • Events: 41
  • p50 / p95 latency: 0.1ms / 2340.0ms
  • Error rate: 14.63%
  • Total cost: $0.0091

**unknown**
  • Events: 21
  • p50 / p95 latency: 210.3ms / 420.0ms
  • Error rate: 0.0%
  • Total cost: $0.0003

**chaos_engineer**
  • Events: 20
  • Error rate: 0.0%

**github_progression**
  • Events: 10
  • p50 / p95 latency: 160.0ms / 1870.0ms
  • Error rate: 0.0%
  • Total cost: $0.0067

**workflow_engine**
  • Events: 10
  • Error rate: 0.0%

**evaluation_system**
  • Events: 6
  • Error rate: 0.0%

**cost_predictor**
  • Events: 6
  • Error rate: 0.0%

**version_manager**
  • Events: 6
  • Error rate: 0.0%

**test_agent**
  • Events: 5
  • p50 / p95 latency: 233.7ms / 1240.0ms
  • Error rate: 0.0%
  • Total cost: $0.0021

**scaffolding_kernel**
  • Events: 5
  • Error rate: 0.0%

**smart_router**
  • Events: 5
  • p50 / p95 latency: 80.2ms / 107.9ms
  • Error rate: 0.0%
  • Total cost: $0.0002

**scaffolder**
  • Events: 3
  • p50 / p95 latency: 2060.0ms / 4120.0ms
  • Error rate: 0.0%
  • Total cost: $0.0145

**health_monitor**
  • Events: 3
  • p50 / p95 latency: 60.8ms / 109.6ms
  • Error rate: 0.0%

**state_kernel**
  • Events: 3
  • Error rate: 0.0%

**deployment_test**
  • Events: 2
  • Error rate: 0.0%

**verification**
  • Events: 2
  • Error rate: 0.0%

**switch**
  • Events: 1
  • Error rate: 0.0%

**test**
  • Events: 1
  • Error rate: 0.0%

## 🔥 Failure Analysis
Total errors detected: 6

  • Pattern: Function 'example_build_website' not registered
    Occurrences: 3
    Last seen: 2026-05-09T03:10:36.137458+00:00

  • Pattern: Function 'example_build_website' not registered and no module path provided
    Occurrences: 3
    Last seen: 2026-05-09T03:11:48.105228+00:00

## 🔧 Suggested Fixes (Automated Autopsy)
Based on observed failure patterns, consider:
  1. Add retry logic with exponential backoff on transient errors
  2. Implement circuit breaker for agents with >5% error rate
  3. Add input validation before expensive LLM calls
  4. Log full prompt when token count exceeds expected range

## 💰 Token & Cost Summary
  • Total prompt tokens: 6,250
  • Total completion tokens: 2,780
  • Estimated total cost: $0.0329

Report generated at: 2026-05-09T03:46:44.045947+00:00