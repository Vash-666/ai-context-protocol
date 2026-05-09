#!/usr/bin/env python3
"""
OpenClaw Trace Analyzer + Automated Failure Autopsy
===================================================
Analyzes structured execution traces and provides:
- Summary statistics (p50/p95 latency, token usage, cost)
- Failure detection and patterns
- Simple "autopsy" suggestions for common failure modes
- Per-agent and per-step breakdowns

Run this daily (or integrate into your health monitor) to get visibility.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import statistics

TRACE_DIR = Path.home() / ".openclaw" / "workspace" / "traces"


def load_traces(days: int = 1) -> List[Dict[str, Any]]:
    """Load traces from the last N days."""
    traces = []
    today = datetime.now(timezone.utc).date()
    
    for i in range(days):
        date = today - timedelta(days=i)
        trace_file = TRACE_DIR / f"traces_{date.strftime('%Y-%m-%d')}.jsonl"
        if trace_file.exists():
            with open(trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
    return traces


def analyze_traces(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform comprehensive analysis on traces."""
    if not traces:
        return {"error": "No traces found"}

    summary = {
        "total_events": len(traces),
        "unique_traces": len(set(t.get("trace_id") for t in traces if t.get("trace_id"))),
        "agents": defaultdict(lambda: {"events": 0, "latencies": [], "errors": 0, "total_cost": 0.0}),
        "event_types": defaultdict(int),
        "errors": [],
        "latency_by_agent_step": defaultdict(list),
        "cost_by_agent": defaultdict(float),
        "token_usage": {"prompt": 0, "completion": 0},
    }

    for trace in traces:
        agent = trace.get("agent") or "unknown"
        event_type = trace.get("event_type", "unknown")
        latency = trace.get("latency_ms")
        error = trace.get("error")
        cost = trace.get("cost_usd") or 0.0
        tokens = trace.get("tokens") or {}

        summary["event_types"][event_type] += 1
        summary["agents"][agent]["events"] += 1
        summary["agents"][agent]["total_cost"] += cost

        if latency and isinstance(latency, (int, float)):
            summary["agents"][agent]["latencies"].append(float(latency))
            step = trace.get("step") or "unknown"
            summary["latency_by_agent_step"][f"{agent}:{step}"].append(latency)

        if error:
            summary["agents"][agent]["errors"] += 1
            summary["errors"].append({
                "timestamp": trace.get("timestamp"),
                "agent": agent,
                "step": trace.get("step"),
                "error": error,
                "trace_id": trace.get("trace_id")
            })

        if tokens.get("prompt"):
            summary["token_usage"]["prompt"] += tokens["prompt"]
        if tokens.get("completion"):
            summary["token_usage"]["completion"] += tokens["completion"]

    # Calculate percentiles
    for agent, data in summary["agents"].items():
        latencies = data["latencies"]
        if latencies:
            data["p50_latency_ms"] = round(float(statistics.median(latencies)), 1)
            data["p95_latency_ms"] = round(
                float(statistics.quantiles(latencies, n=20)[18]) if len(latencies) >= 20 else float(max(latencies)), 1
            )
            data["avg_latency_ms"] = round(float(statistics.mean(latencies)), 1)
        data["error_rate"] = round(data["errors"] / data["events"] * 100, 2) if data["events"] > 0 else 0

    return summary


def generate_autopsy_report(summary: Dict[str, Any]) -> str:
    """Generate human-readable autopsy + recommendations."""
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════════╗")
    lines.append("║           OpenClaw Execution Autopsy Report                      ║")
    lines.append("╚══════════════════════════════════════════════════════════════════╝")
    lines.append("")

    if "error" in summary:
        lines.append(f"❌ {summary['error']}")
        return "\n".join(lines)

    lines.append(f"📊 Analyzed {summary['total_events']} events across {summary['unique_traces']} traces")
    lines.append("")

    # Agent Performance
    lines.append("## Agent Performance")
    for agent, data in sorted(summary["agents"].items(), key=lambda x: -x[1]["events"]):
        lines.append(f"\n**{agent}**")
        lines.append(f"  • Events: {data['events']}")
        if data.get("p95_latency_ms"):
            lines.append(f"  • p50 / p95 latency: {data.get('p50_latency_ms')}ms / {data.get('p95_latency_ms')}ms")
        lines.append(f"  • Error rate: {data.get('error_rate', 0)}%")
        if data.get("total_cost", 0) > 0:
            lines.append(f"  • Total cost: ${data['total_cost']:.4f}")

    # Failure Analysis
    if summary["errors"]:
        lines.append("\n## 🔥 Failure Analysis")
        lines.append(f"Total errors detected: {len(summary['errors'])}")
        
        # Group errors by type
        error_patterns = defaultdict(list)
        for err in summary["errors"]:
            key = err.get("error", "Unknown")[:80]
            error_patterns[key].append(err)

        for pattern, occurrences in sorted(error_patterns.items(), key=lambda x: -len(x[1]))[:5]:
            lines.append(f"\n  • Pattern: {pattern}")
            lines.append(f"    Occurrences: {len(occurrences)}")
            if occurrences:
                lines.append(f"    Last seen: {occurrences[-1]['timestamp']}")

        lines.append("\n## 🔧 Suggested Fixes (Automated Autopsy)")
        lines.append("Based on observed failure patterns, consider:")
        lines.append("  1. Add retry logic with exponential backoff on transient errors")
        lines.append("  2. Implement circuit breaker for agents with >5% error rate")
        lines.append("  3. Add input validation before expensive LLM calls")
        lines.append("  4. Log full prompt when token count exceeds expected range")
    else:
        lines.append("\n✅ No errors detected in the analyzed window. Great job!")

    # Token & Cost Summary
    lines.append("\n## 💰 Token & Cost Summary")
    lines.append(f"  • Total prompt tokens: {summary['token_usage']['prompt']:,}")
    lines.append(f"  • Total completion tokens: {summary['token_usage']['completion']:,}")
    total_cost = sum(a["total_cost"] for a in summary["agents"].values())
    lines.append(f"  • Estimated total cost: ${total_cost:.4f}")

    lines.append("")
    lines.append("Report generated at: " + datetime.now(timezone.utc).isoformat())
    return "\n".join(lines)


def main():
    print("🔍 OpenClaw Trace Analyzer")
    print("Loading traces from the last 7 days...\n")

    traces = load_traces(days=7)
    if not traces:
        print("No traces found yet. Run your agents with execution_tracer.py first.")
        return

    summary = analyze_traces(traces)
    report = generate_autopsy_report(summary)

    print(report)

    # Also save report
    report_file = TRACE_DIR / f"autopsy_report_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 Full report saved to: {report_file}")


if __name__ == "__main__":
    main()