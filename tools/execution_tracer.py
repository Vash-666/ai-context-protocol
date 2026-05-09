#!/usr/bin/env python3
"""
OpenClaw Execution Tracer
=========================
Core instrumentation library for structured tracing of agent execution.

Features:
- Structured JSON traces (not plain text logs)
- Automatic latency, token, and cost tracking
- Input/output content hashing for debugging
- Hierarchical traces (parent/child relationships)
- Easy decorator and context manager usage
- JSONL storage (simple, queryable, no database needed)

Usage:
    from execution_tracer import tracer, TraceContext

    with TraceContext(agent="website_builder", step="generate_html"):
        # your code here
        tracer.record_llm_call(model="gemini-1.5", prompt_tokens=1200, completion_tokens=450)

    # Or use decorator
    @tracer.trace(agent="github_progression", step="analyze_repo")
    def my_function(...):
        ...
"""

import json
import time
import hashlib
import uuid
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional, Callable
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
TRACE_DIR = Path.home() / ".openclaw" / "workspace" / "traces"
TRACE_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_TRACE_FILE = TRACE_DIR / f"traces_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

# In-memory current trace context (simple thread-local style for single process)
_current_trace: Dict[str, Any] = {}


def _get_trace_id() -> str:
    return str(uuid.uuid4())


def _hash_content(content: Any) -> str:
    """Create a stable hash of input/output content for debugging without storing full data."""
    if content is None:
        return "null"
    try:
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.sha256(str(content).encode()).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_trace(record: Dict[str, Any]) -> None:
    """Append a structured trace record to today's JSONL file."""
    record["timestamp"] = _now_iso()
    with open(CURRENT_TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
class ExecutionTracer:
    """Main tracer class. Use the global `tracer` instance."""

    def __init__(self):
        self.current_trace_id: Optional[str] = None
        self.parent_trace_id: Optional[str] = None

    def start_trace(
        self,
        agent: str,
        step: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new root trace or child trace."""
        trace_id = _get_trace_id()
        self.current_trace_id = trace_id

        record = {
            "trace_id": trace_id,
            "parent_trace_id": self.parent_trace_id,
            "event_type": "trace_start",
            "agent": agent,
            "step": step,
            "metadata": metadata or {},
        }
        _write_trace(record)
        _current_trace["trace_id"] = trace_id
        _current_trace["agent"] = agent
        _current_trace["step"] = step
        return trace_id

    def end_trace(self, status: str = "success", metadata: Optional[Dict[str, Any]] = None):
        """End the current trace."""
        if not self.current_trace_id:
            return

        record = {
            "trace_id": self.current_trace_id,
            "event_type": "trace_end",
            "status": status,
            "metadata": metadata or {},
        }
        _write_trace(record)
        self.current_trace_id = None
        _current_trace.clear()

    def record_event(
        self,
        event_type: str,
        agent: Optional[str] = None,
        step: Optional[str] = None,
        latency_ms: Optional[float] = None,
        model: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        input_data: Any = None,
        output_data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """Record any execution event with rich structured data."""
        trace_id = self.current_trace_id or _current_trace.get("trace_id") or _get_trace_id()

        record = {
            "trace_id": trace_id,
            "event_type": event_type,
            "agent": agent or _current_trace.get("agent"),
            "step": step or _current_trace.get("step"),
            "latency_ms": latency_ms,
            "model": model,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": (prompt_tokens or 0) + (completion_tokens or 0)
            } if prompt_tokens or completion_tokens else None,
            "cost_usd": cost_usd,
            "input_hash": _hash_content(input_data) if input_data else None,
            "output_hash": _hash_content(output_data) if output_data else None,
            "error": error,
            "metadata": metadata or {},
        }
        _write_trace(record)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost_usd: Optional[float] = None,
        input_data: Any = None,
        output_data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method for LLM calls."""
        self.record_event(
            event_type="llm_call",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            input_data=input_data,
            output_data=output_data,
            metadata=metadata,
        )

    def record_tool_call(
        self,
        tool_name: str,
        latency_ms: float,
        input_data: Any = None,
        output_data: Any = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method for tool/function calls."""
        self.record_event(
            event_type="tool_call",
            step=tool_name,
            latency_ms=latency_ms,
            input_data=input_data,
            output_data=output_data,
            error=error,
            metadata={"success": success, **(metadata or {})},
        )

    def record_transition(
        self,
        from_step: str,
        to_step: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record state/agent transitions."""
        self.record_event(
            event_type="transition",
            step=f"{from_step} → {to_step}",
            metadata=metadata,
        )

    @contextmanager
    def trace(
        self,
        agent: str,
        step: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing a block of code."""
        trace_id = self.start_trace(agent=agent, step=step, metadata=metadata)
        start_time = time.time()
        status = "success"
        try:
            yield trace_id
        except Exception as e:
            status = "error"
            self.record_event(
                event_type="error",
                error=str(e),
                metadata={"exception_type": type(e).__name__}
            )
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            self.record_event(
                event_type="trace_block_end",
                latency_ms=round(latency_ms, 2),
            )
            self.end_trace(status=status)

    def trace_decorator(self, agent: str, step: Optional[str] = None):
        """Decorator for tracing entire functions."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                step_name = step or func.__name__
                with self.trace(agent=agent, step=step_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator


# Global singleton instance
tracer = ExecutionTracer()


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage (for testing)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Testing OpenClaw Execution Tracer...")

    # Example 1: Using context manager
    with tracer.trace(agent="test_agent", step="example_workflow"):
        tracer.record_event("info", metadata={"message": "Starting test workflow"})
        
        # Simulate LLM call
        time.sleep(0.1)
        tracer.record_llm_call(
            model="gemini-embedding-001",
            prompt_tokens=850,
            completion_tokens=320,
            latency_ms=1240,
            cost_usd=0.0021,
            input_data={"prompt": "Build a landing page for a coffee shop"},
            output_data={"html": "<html>...</html>"}
        )

        # Simulate tool call
        time.sleep(0.05)
        tracer.record_tool_call(
            tool_name="write_file",
            latency_ms=87,
            input_data={"path": "index.html"},
            output_data={"bytes_written": 12400},
            success=True
        )

    print(f"✅ Traces written to: {CURRENT_TRACE_FILE}")
    print("   You can now run trace_analyzer.py to inspect them.")