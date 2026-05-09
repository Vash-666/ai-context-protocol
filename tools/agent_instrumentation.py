#!/usr/bin/env python3
"""
OpenClaw Agent Instrumentation Examples
=======================================
Ready-to-use patterns to add tracing to your real agents.

Copy the relevant sections into your existing agent code
(website builder, @switch, github progression, etc.)
"""

from execution_tracer import tracer
import time

# =============================================================================
# PATTERN 1: Basic Agent Workflow (Recommended)
# =============================================================================
def example_basic_agent_workflow():
    """
    Use this pattern for most agent tasks.
    Wrap the entire task in a trace context.
    """
    with tracer.trace(agent="website_builder", step="build_landing_page"):
        # Your existing logic here...
        print("Starting website build...")

        # Record LLM calls
        tracer.record_llm_call(
            model="gemini-1.5-pro",
            prompt_tokens=1450,
            completion_tokens=720,
            latency_ms=2340,
            cost_usd=0.0091,
            input_data={"task": "Create modern landing page for coffee shop"},
            output_data={"files_created": ["index.html", "style.css"]}
        )

        # Record tool calls
        tracer.record_tool_call(
            tool_name="write_file",
            latency_ms=48,
            input_data={"path": "index.html"},
            output_data={"bytes": 18400},
            success=True
        )

        print("Website build completed successfully!")


# =============================================================================
# PATTERN 2: Multi-Step Agent with Transitions
# =============================================================================
def example_multi_step_agent():
    """
    Use this when your agent has clear stages (research → plan → execute → review)
    """
    with tracer.trace(agent="github_progression", step="daily_sync"):
        # Step 1: Research / Fetch data
        with tracer.trace(agent="github_progression", step="fetch_repos"):
            tracer.record_llm_call(
                model="claude-sonnet-4-5",
                prompt_tokens=890,
                completion_tokens=310,
                latency_ms=1870,
                cost_usd=0.0048
            )

        # Record transition
        tracer.record_transition("fetch_repos", "analyze_changes")

        # Step 2: Analyze
        with tracer.trace(agent="github_progression", step="analyze_changes"):
            tracer.record_tool_call(
                tool_name="run_git_commands",
                latency_ms=320,
                success=True
            )

        # Step 3: Execute actions
        with tracer.trace(agent="github_progression", step="create_progress_report"):
            tracer.record_llm_call(
                model="gemini-2.5-flash",
                prompt_tokens=620,
                completion_tokens=480,
                latency_ms=980,
                cost_usd=0.0019
            )


# =============================================================================
# PATTERN 3: Error Handling + Automatic Capture
# =============================================================================
def example_with_error_handling():
    """
    Errors are automatically captured when using the context manager.
    """
    try:
        with tracer.trace(agent="scaffolder", step="generate_skill"):
            # Simulate something that might fail
            tracer.record_llm_call(
                model="grok-3",
                prompt_tokens=2100,
                completion_tokens=950,
                latency_ms=4120,
                cost_usd=0.0145
            )
            # If an exception happens here, it will be recorded automatically
            # raise Exception("Simulated failure")
    except Exception as e:
        print(f"Agent failed: {e}")
        # The tracer already recorded the error + traceback info


# =============================================================================
# PATTERN 4: Quick One-off LLM Call (when you don't want full context)
# =============================================================================
def example_quick_llm_call():
    """Use this for simple, standalone LLM calls outside a bigger workflow."""
    tracer.record_llm_call(
        model="gemini-embedding-001",
        prompt_tokens=340,
        completion_tokens=0,
        latency_ms=420,
        cost_usd=0.0003,
        metadata={"purpose": "embedding_for_rag"}
    )


# =============================================================================
# PATTERN 5: Wrapping Existing Functions (Decorator)
# =============================================================================
@tracer.trace_decorator(agent="health_monitor", step="check_system_health")
def check_system_health():
    """Your existing health check function - now automatically traced."""
    print("Running health checks...")
    time.sleep(0.1)  # Simulate work

    tracer.record_tool_call(
        tool_name="check_disk_space",
        latency_ms=12,
        success=True
    )
    return {"status": "healthy"}


# =============================================================================
# HOW TO USE THESE PATTERNS
# =============================================================================
if __name__ == "__main__":
    print("=== Testing Instrumentation Patterns ===\n")

    print("1. Basic workflow:")
    example_basic_agent_workflow()

    print("\n2. Multi-step agent:")
    example_multi_step_agent()

    print("\n3. With error handling:")
    example_with_error_handling()

    print("\n4. Quick LLM call:")
    example_quick_llm_call()

    print("\n5. Decorated function:")
    check_system_health()

    print("\n✅ All patterns tested. Check your traces/ folder for output.")