#!/usr/bin/env python3
"""
OpenClaw Autopsy Agent (Priority 1b)
====================================
Automated Failure Analysis + Improvement Suggestions using Grok API.

What it does:
- Scans recent execution traces
- Finds recurring problems and failure patterns
- Sends summarized failures to Grok for intelligent analysis
- Generates a clear, actionable daily report with specific recommendations

Usage:
    python autopsy_agent.py

    # Dry run (no Grok API calls)
    python autopsy_agent.py --dry-run

Requirements:
    pip install openai
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional
import statistics

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
TRACE_DIR = Path.home() / ".openclaw" / "workspace" / "traces"
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Grok API settings (xAI)
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-3-latest"          # or "grok-2-latest" depending on availability

# Analysis settings
DAYS_TO_ANALYZE = 3
MAX_FAILURES_TO_ANALYZE = 8           # Limit how many failures we send to Grok (cost control)
DRY_RUN = "--dry-run" in sys.argv


# ─────────────────────────────────────────────────────────────────────────────
# Trace Loading & Basic Analysis
# ─────────────────────────────────────────────────────────────────────────────
def load_recent_traces(days: int = DAYS_TO_ANALYZE) -> List[Dict[str, Any]]:
    traces = []
    today = datetime.now(timezone.utc).date()

    for i in range(days):
        date = today - timedelta(days=i)
        trace_file = TRACE_DIR / f"traces_{date.strftime('%Y-%m-%d')}.jsonl"
        if trace_file.exists():
            with open(trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            traces.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    return traces


def analyze_traces(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not traces:
        return {"error": "No traces found in the last few days."}

    summary = {
        "total_events": len(traces),
        "unique_traces": len({t.get("trace_id") for t in traces if t.get("trace_id")}),
        "agents": defaultdict(lambda: {"events": 0, "errors": 0, "latencies": [], "total_cost": 0.0}),
        "errors": [],
        "high_latency_steps": [],
    }

    for t in traces:
        agent = t.get("agent") or "unknown"
        latency = t.get("latency_ms")
        error = t.get("error")
        cost = t.get("cost_usd") or 0.0

        summary["agents"][agent]["events"] += 1
        summary["agents"][agent]["total_cost"] += cost

        if latency and isinstance(latency, (int, float)):
            summary["agents"][agent]["latencies"].append(float(latency))

        if error:
            summary["agents"][agent]["errors"] += 1
            summary["errors"].append({
                "timestamp": t.get("timestamp"),
                "agent": agent,
                "step": t.get("step"),
                "error": error,
                "trace_id": t.get("trace_id"),
                "model": t.get("model"),
            })

    # Calculate stats
    for agent, data in summary["agents"].items():
        latencies = data["latencies"]
        if latencies:
            data["p50"] = round(float(statistics.median(latencies)), 1)
            data["p95"] = round(float(statistics.quantiles(latencies, n=20)[18]) if len(latencies) >= 20 else float(max(latencies)), 1)
        data["error_rate"] = round((data["errors"] / data["events"]) * 100, 2) if data["events"] > 0 else 0

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Grok API Call
# ─────────────────────────────────────────────────────────────────────────────
def call_grok_for_analysis(failure_cluster: Dict[str, Any]) -> str:
    """Send a failure pattern to Grok and get improvement suggestions."""
    if not GROK_API_KEY:
        return "ERROR: GROK_API_KEY environment variable is not set."

    if DRY_RUN:
        return "[DRY RUN] Would have called Grok API with this failure cluster."

    try:
        from openai import OpenAI
    except ImportError:
        return "ERROR: 'openai' package not installed. Run: pip install openai"

    client = OpenAI(
        api_key=GROK_API_KEY,
        base_url=GROK_BASE_URL,
    )

    prompt = f"""You are an expert AI systems debugger.

Here is a cluster of failures from an autonomous agent system:

Agent: {failure_cluster.get('agent')}
Step: {failure_cluster.get('step')}
Error message: {failure_cluster.get('error')}
Occurrences: {failure_cluster.get('count')}
Model used: {failure_cluster.get('model', 'unknown')}
Average latency: {failure_cluster.get('avg_latency', 'N/A')} ms

Please do the following:
1. Identify the most likely root cause.
2. Give 2-3 concrete, actionable suggestions to fix or prevent this issue.
3. If relevant, suggest improvements to the prompt or workflow.

Keep your answer concise and practical."""

    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": "You are a highly skilled AI debugging assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR calling Grok API: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# Report Generation
# ─────────────────────────────────────────────────────────────────────────────
def generate_report(summary: Dict[str, Any], grok_analyses: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("# OpenClaw Autopsy Report")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Period analyzed:** Last {DAYS_TO_ANALYZE} days")
    lines.append("")

    if "error" in summary:
        lines.append(f"❌ {summary['error']}")
        return "\n".join(lines)

    # Overview
    lines.append("## 📊 Overview")
    lines.append(f"- Total events analyzed: **{summary['total_events']}**")
    lines.append(f"- Unique traces: **{summary['unique_traces']}**")
    lines.append("")

    # Agent Health
    lines.append("## 🤖 Agent Health Summary")
    for agent, data in sorted(summary["agents"].items(), key=lambda x: -x[1]["events"]):
        lines.append(f"### {agent}")
        lines.append(f"- Events: {data['events']}")
        if data.get("p50"):
            lines.append(f"- Latency (p50 / p95): {data['p50']}ms / {data['p95']}ms")
        lines.append(f"- Error rate: **{data.get('error_rate', 0)}%**")
        if data.get("total_cost", 0) > 0:
            lines.append(f"- Estimated cost: ${data['total_cost']:.4f}")
        lines.append("")

    # Failures analyzed by Grok
    if grok_analyses:
        lines.append("## 🔍 Grok's Analysis & Recommendations")
        for item in grok_analyses:
            lines.append(f"### Failure: {item['agent']} → {item['step']}")
            lines.append(f"**Error:** {item['error'][:120]}...")
            lines.append(f"**Occurrences:** {item['count']}")
            lines.append("")
            lines.append("**Grok's Suggestions:**")
            lines.append(item['analysis'])
            lines.append("")
            lines.append("---")
    else:
        lines.append("## ✅ No major failures detected")
        lines.append("Everything looks healthy in the analyzed period.")

    lines.append("")
    lines.append("---")
    lines.append("*Report generated by OpenClaw Autopsy Agent (using Grok)*")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    global DRY_RUN
    print("🧠 OpenClaw Autopsy Agent starting...")

    if not GROK_API_KEY and not DRY_RUN:
        print("⚠️  Warning: GROK_API_KEY is not set. Running in dry-run mode.")
        DRY_RUN = True

    traces = load_recent_traces()
    if not traces:
        print("No traces found. Make sure your agents are using execution_tracer.py")
        return

    summary = analyze_traces(traces)

    # Prepare failure clusters for Grok
    failure_clusters = []
    error_groups = defaultdict(list)
    for err in summary.get("errors", []):
        key = (err["agent"], err["step"], err.get("error", "")[:80])
        error_groups[key].append(err)

    for (agent, step, error_text), errors in sorted(error_groups.items(), key=lambda x: -len(x[1]))[:MAX_FAILURES_TO_ANALYZE]:
        cluster = {
            "agent": agent,
            "step": step,
            "error": error_text,
            "count": len(errors),
            "model": errors[0].get("model") if errors else None,
        }
        failure_clusters.append(cluster)

    # Get Grok analysis for each cluster
    grok_analyses = []
    for cluster in failure_clusters:
        print(f"   Analyzing failure: {cluster['agent']} → {cluster['step']} ({cluster['count']} times)...")
        analysis = call_grok_for_analysis(cluster)
        grok_analyses.append({
            **cluster,
            "analysis": analysis
        })

    # Generate final report
    report = generate_report(summary, grok_analyses)

    # Save report
    report_filename = f"autopsy_report_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    report_path = REPORTS_DIR / report_filename
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Autopsy report saved to: {report_path}")
    print("\n" + "="*60)
    print(report)
    print("="*60)


if __name__ == "__main__":
    main()