# Execution Tracing Integration Guide

## Grok Priority 1: Execution Tracing + Automated Failure Autopsy

### What You Just Got

A production-grade execution tracer that records **structured JSON traces** of every agent action — not plain text logs.

### Features

- **Structured JSONL storage** — Queryable, no database needed
- **Automatic metrics** — Latency, tokens, cost per call
- **Content hashing** — Debug without storing full data
- **Hierarchical traces** — Parent/child relationships for spawn chains
- **Zero overhead** — Simple Python, no external dependencies

### Storage Location

```
~/.openclaw/workspace/traces/
└── traces_2026-05-09.jsonl  # One file per day
```

### Quick Start

#### 1. Trace a Code Block (Context Manager)

```python
from execution_tracer import tracer

with tracer.trace(agent="website_builder", step="generate_html"):
    # Your code here
    result = build_website()
    
    tracer.record_llm_call(
        model="claude-sonnet-4-5",
        prompt_tokens=1500,
        completion_tokens=890,
        latency_ms=3400,
        cost_usd=0.0089,
        input_data={"prompt": "Build a landing page..."},
        output_data={"html": result}
    )
```

#### 2. Trace a Function (Decorator)

```python
from execution_tracer import tracer

@tracer.trace_decorator(agent="github_progression", step="analyze_repo")
def analyze_repository(repo_url):
    # Your code here
    return analysis_results
```

#### 3. Record Custom Events

```python
tracer.record_event(
    event_type="spawn_start",
    agent="scaffolder",
    step="create_website",
    metadata={"project": "sharonville-real-estate"}
)
```

### Viewing Traces

```bash
# See today's traces
ls -la ~/.openclaw/workspace/traces/

# View last 10 entries
tail -10 ~/.openclaw/workspace/traces/traces_2026-05-09.jsonl | jq

# Search for errors
grep '"error":' ~/.openclaw/workspace/traces/traces_2026-05-09.jsonl

# Calculate total cost today
cat ~/.openclaw/workspace/traces/traces_2026-05-09.jsonl | \
  jq -s 'map(select(.cost_usd != null).cost_usd) | add'
```

### What Gets Recorded

Every trace includes:
- `trace_id` — Unique identifier
- `event_type` — trace_start, llm_call, tool_call, error, etc.
- `agent` — Which agent executed
- `step` — What step/action
- `latency_ms` — How long it took
- `model` — LLM model used
- `tokens` — {prompt, completion, total}
- `cost_usd` — Cost of operation
- `input_hash` / `output_hash` — Content fingerprints
- `timestamp` — ISO 8601 timestamp
- `error` — Error message if failed

### Autopsy Agents

You now have **two** autopsy tools:

#### 1. trace_analyzer.py (Basic)
```bash
python3 tools/trace_analyzer.py
```
**Features:** Local analysis, p50/p95 latency, cost tracking, basic suggestions

#### 2. autopsy_agent.py (Grok-Powered) ⭐ Recommended
```bash
python3 tools/autopsy_agent.py
```
**Features:** 
- **Grok API integration** — Intelligent failure analysis
- **Root cause identification** — AI-powered debugging
- **Concrete recommendations** — Specific fixes for each failure pattern
- **Failure clustering** — Groups similar errors automatically
- **Cost-controlled** — Limits API calls to MAX_FAILURES_TO_ANALYZE (default: 8)

**Example Output:**
```
# OpenClaw Autopsy Report
**Generated:** 2026-05-09 03:02 UTC

## 🤖 Agent Health Summary
### test_agent
- Events: 5
- Latency (p50 / p95): 233.7ms / 1240ms
- Error rate: 0.0%
- Estimated cost: $0.0021

## 🔍 Grok's Analysis & Recommendations
### Failure: scaffolder → build_website
**Error:** LLM timeout after 30s...
**Occurrences:** 3

**Grok's Suggestions:**
1. Add retry logic with exponential backoff
2. Implement circuit breaker for slow LLM calls
3. Consider using faster model (Gemini Flash) for initial scaffolding
```

**Integration with Health Monitor:**
Add to your daily health check:
```bash
# In automated-health-monitor.sh
python3 /Users/rohitvashist/.openclaw/workspace/tools/autopsy_agent.py >> "$REPORT_FILE"
```

**Dry-run mode (no API calls):**
```bash
python3 tools/autopsy_agent.py --dry-run
```

### Integration with Existing System

To trace your existing agents, wrap their main execution:

```python
# In your agent code
from execution_tracer import tracer

def agent_main(task):
    with tracer.trace(agent="quality", step=task["name"]):
        # Existing agent logic
        result = process_task(task)
        
        # Record metrics
        tracer.record_event(
            event_type="agent_complete",
            latency_ms=calculate_latency(),
            metadata={"success": True, "output_size": len(result)}
        )
        
        return result
```

### Cost Attribution

Track costs per project:

```python
tracer.record_event(
    event_type="project_start",
    agent="switch",
    step="route_task",
    metadata={"project": "sharonville-real-estate", "budget": 5.00}
)
```

Then query:
```bash
cat traces_2026-05-09.jsonl | \
  jq 'select(.metadata.project == "sharonville-real-estate") | .cost_usd' | \
  jq -s 'add'
```

### Status

✅ **COMPLETE** — Grok Priority 1 (Execution Tracing)  
✅ **COMPLETE** — Priority 1b (Autopsy Agent)  
🔄 **NEXT** — Priority 2 (Worker Queue)

---

**Built:** 2026-05-08  
**Source:** `/Users/rohitvashist/Downloads/execution_tracer.py`  
**Installed:** `/Users/rohitvashist/.openclaw/workspace/tools/execution_tracer.py`
