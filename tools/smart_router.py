#!/usr/bin/env python3
"""
OpenClaw Smart Router v3 (Priority 4)
======================================
Cost-optimized model routing with automatic escalation.

Grok's words: "Smart Router v2 is almost certainly overusing heavy models."

Features:
- 80% tasks → Gemini Flash (cheap)
- 20% tasks → Claude/Sonnet (complex)
- Cost/latency budget per task
- Automatic escalation on failure
- 3-5x cost reduction target

Usage:
    from smart_router import SmartRouter, TaskComplexity
    
    router = SmartRouter()
    
    # Router automatically selects model
    result = router.route(
        task_type="website_build",
        prompt="Build a landing page...",
        max_cost=0.05  # Budget constraint
    )
"""

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import re

# Import tracer if available
try:
    from execution_tracer import tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TaskComplexity(Enum):
    """Task complexity levels determine routing."""
    SIMPLE = "simple"      # Gemini Flash, $0.0001-0.001
    MODERATE = "moderate"  # Gemini Pro, $0.001-0.01
    COMPLEX = "complex"    # Claude Sonnet, $0.01-0.1
    CRITICAL = "critical"  # Claude Opus, $0.1+


# Model pricing (per 1K tokens, approximate)
MODEL_PRICING = {
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
    "claude-opus-4": {"input": 0.015, "output": 0.075},
}

# Routing matrix: task type → default complexity
TASK_COMPLEXITY_MAP = {
    # Simple tasks → Flash
    "embedding": TaskComplexity.SIMPLE,
    "summarize_short": TaskComplexity.SIMPLE,
    "keyword_extract": TaskComplexity.SIMPLE,
    "format_convert": TaskComplexity.SIMPLE,
    "cache_lookup": TaskComplexity.SIMPLE,
    "simple_qa": TaskComplexity.SIMPLE,
    
    # Moderate tasks → Pro
    "website_build": TaskComplexity.MODERATE,
    "content_rewrite": TaskComplexity.MODERATE,
    "code_review": TaskComplexity.MODERATE,
    "test_generate": TaskComplexity.MODERATE,
    "doc_analyze": TaskComplexity.MODERATE,
    
    # Complex tasks → Sonnet
    "architecture_design": TaskComplexity.COMPLEX,
    "multi_step_reasoning": TaskComplexity.COMPLEX,
    "creative_writing": TaskComplexity.COMPLEX,
    "debug_complex": TaskComplexity.COMPLEX,
    "synthesis": TaskComplexity.COMPLEX,
    
    # Critical tasks → Opus
    "security_audit": TaskComplexity.CRITICAL,
    "production_deploy": TaskComplexity.CRITICAL,
    "financial_analysis": TaskComplexity.CRITICAL,
}

# Complexity → model mapping
COMPLEXITY_MODEL_MAP = {
    TaskComplexity.SIMPLE: "gemini-2.5-flash",
    TaskComplexity.MODERATE: "gemini-1.5-pro",
    TaskComplexity.COMPLEX: "claude-sonnet-4-5",
    TaskComplexity.CRITICAL: "claude-opus-4",
}

# Default budgets per complexity
DEFAULT_BUDGETS = {
    TaskComplexity.SIMPLE: 0.001,
    TaskComplexity.MODERATE: 0.01,
    TaskComplexity.COMPLEX: 0.1,
    TaskComplexity.CRITICAL: 1.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class RoutingDecision:
    task_type: str
    complexity: TaskComplexity
    model: str
    budget_usd: float
    estimated_tokens: int
    estimated_cost: float
    reason: str


@dataclass
class RoutingResult:
    task_type: str
    model_used: str
    complexity: TaskComplexity
    success: bool
    latency_ms: float
    actual_cost: float
    tokens_input: int
    tokens_output: int
    escalated: bool
    timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Complexity Analyzer
# ─────────────────────────────────────────────────────────────────────────────
def analyze_complexity(prompt: str, task_type: Optional[str] = None) -> TaskComplexity:
    """
    Analyze prompt complexity to determine routing.
    
    Factors:
    - Prompt length (longer = more complex)
    - Presence of complex keywords
    - Multi-step requirements
    - Code/specialized content
    """
    prompt_lower = prompt.lower()
    
    # Check for critical patterns
    critical_patterns = [
        r"security", r"audit", r"vulnerability", r"exploit",
        r"production", r"deploy", r"financial", r"compliance",
        r"legal", r"regulatory"
    ]
    for pattern in critical_patterns:
        if re.search(pattern, prompt_lower):
            return TaskComplexity.CRITICAL
    
    # Check for complex patterns
    complex_patterns = [
        r"architecture", r"design.*system", r"multi.step",
        r"compare.*contrast", r"synthesize", r"creative",
        r"debug.*complex", r"troubleshoot", r"optimize"
    ]
    complex_score = sum(1 for p in complex_patterns if re.search(p, prompt_lower))
    
    # Check for simple patterns
    simple_patterns = [
        r"summarize", r"extract", r"keyword", r"format",
        r"convert", r"short", r"brief", r"list"
    ]
    simple_score = sum(1 for p in simple_patterns if re.search(p, prompt_lower))
    
    # Length factor
    length_score = len(prompt) / 1000  # Score per 1K chars
    
    # Calculate complexity score
    if complex_score >= 2 or length_score > 5:
        return TaskComplexity.COMPLEX
    elif simple_score >= 2 and complex_score == 0:
        return TaskComplexity.SIMPLE
    else:
        return TaskComplexity.MODERATE


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)."""
    return len(text) // 4


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a model call."""
    pricing = MODEL_PRICING.get(model, {"input": 0.01, "output": 0.03})
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)


# ─────────────────────────────────────────────────────────────────────────────
# Smart Router
# ─────────────────────────────────────────────────────────────────────────────
class SmartRouter:
    """
    Cost-optimized model router with automatic escalation.
    """
    
    def __init__(self):
        self.stats = {
            "total_routes": 0,
            "by_complexity": {c: {"count": 0, "cost": 0.0} for c in TaskComplexity},
            "escalations": 0,
            "cost_savings": 0.0,
        }
        self.history: List[RoutingResult] = []
    
    def route(
        self,
        task_type: str,
        prompt: str,
        max_cost: Optional[float] = None,
        force_complexity: Optional[TaskComplexity] = None,
    ) -> RoutingDecision:
        """
        Determine optimal model routing for a task.
        
        Returns:
            RoutingDecision with model, budget, and reasoning.
        """
        # Determine complexity
        if force_complexity:
            complexity = force_complexity
        elif task_type in TASK_COMPLEXITY_MAP:
            complexity = TASK_COMPLEXITY_MAP[task_type]
        else:
            complexity = analyze_complexity(prompt, task_type)
        
        # Select model
        model = COMPLEXITY_MODEL_MAP[complexity]
        
        # Determine budget
        budget = max_cost or DEFAULT_BUDGETS[complexity]
        
        # Estimate tokens and cost
        estimated_input = estimate_tokens(prompt)
        estimated_output = estimated_input // 2  # Rough estimate
        estimated_cost = estimate_cost(model, estimated_input, estimated_output)
        
        # Generate reasoning
        reasons = {
            TaskComplexity.SIMPLE: "Short/simple task → use cheap model",
            TaskComplexity.MODERATE: "Standard task → balanced model",
            TaskComplexity.COMPLEX: "Complex reasoning → powerful model",
            TaskComplexity.CRITICAL: "High stakes → best model",
        }
        
        decision = RoutingDecision(
            task_type=task_type,
            complexity=complexity,
            model=model,
            budget_usd=budget,
            estimated_tokens=estimated_input + estimated_output,
            estimated_cost=estimated_cost,
            reason=reasons[complexity]
        )
        
        # Trace routing decision
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="routing_decision",
                agent="smart_router",
                step=task_type,
                metadata={
                    "model": model,
                    "complexity": complexity.value,
                    "estimated_cost": estimated_cost,
                    "budget": budget
                }
            )
        
        return decision
    
    def execute_with_fallback(
        self,
        task_type: str,
        prompt: str,
        llm_caller: Callable[[str, str], Tuple[str, int, int]],
        max_cost: Optional[float] = None,
    ) -> RoutingResult:
        """
        Execute task with automatic escalation on failure.
        
        Args:
            task_type: Type of task
            prompt: The prompt to send
            llm_caller: Function(model, prompt) -> (output, input_tokens, output_tokens)
            max_cost: Maximum budget for this task
        
        Returns:
            RoutingResult with actual metrics
        """
        start_time = time.time() * 1000
        
        # Get routing decision
        decision = self.route(task_type, prompt, max_cost)
        
        # Try primary model
        try:
            output, input_tokens, output_tokens = llm_caller(decision.model, prompt)
            actual_cost = estimate_cost(decision.model, input_tokens, output_tokens)
            
            result = RoutingResult(
                task_type=task_type,
                model_used=decision.model,
                complexity=decision.complexity,
                success=True,
                latency_ms=time.time() * 1000 - start_time,
                actual_cost=actual_cost,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                escalated=False,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            # Escalate to next tier
            escalation_map = {
                TaskComplexity.SIMPLE: TaskComplexity.MODERATE,
                TaskComplexity.MODERATE: TaskComplexity.COMPLEX,
                TaskComplexity.COMPLEX: TaskComplexity.CRITICAL,
                TaskComplexity.CRITICAL: None  # No escalation possible
            }
            
            next_complexity = escalation_map.get(decision.complexity)
            if next_complexity and (max_cost is None or DEFAULT_BUDGETS[next_complexity] <= max_cost):
                # Escalate
                escalation_model = COMPLEXITY_MODEL_MAP[next_complexity]
                output, input_tokens, output_tokens = llm_caller(escalation_model, prompt)
                actual_cost = estimate_cost(escalation_model, input_tokens, output_tokens)
                
                result = RoutingResult(
                    task_type=task_type,
                    model_used=escalation_model,
                    complexity=next_complexity,
                    success=True,
                    latency_ms=time.time() * 1000 - start_time,
                    actual_cost=actual_cost,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    escalated=True,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.stats["escalations"] += 1
            else:
                # No escalation possible
                result = RoutingResult(
                    task_type=task_type,
                    model_used=decision.model,
                    complexity=decision.complexity,
                    success=False,
                    latency_ms=time.time() * 1000 - start_time,
                    actual_cost=0.0,
                    tokens_input=0,
                    tokens_output=0,
                    escalated=False,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        # Update stats
        self.stats["total_routes"] += 1
        self.stats["by_complexity"][result.complexity]["count"] += 1
        self.stats["by_complexity"][result.complexity]["cost"] += result.actual_cost
        self.history.append(result)
        
        # Calculate savings vs using most expensive model
        expensive_cost = estimate_cost("claude-opus-4", result.tokens_input, result.tokens_output)
        savings = expensive_cost - result.actual_cost
        self.stats["cost_savings"] += max(0, savings)
        
        # Trace execution
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="routing_execution",
                agent="smart_router",
                step=task_type,
                latency_ms=result.latency_ms,
                cost_usd=result.actual_cost,
                metadata={
                    "model": result.model_used,
                    "success": result.success,
                    "escalated": result.escalated,
                    "tokens": result.tokens_input + result.tokens_output
                }
            )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total_cost = sum(
            data["cost"] for data in self.stats["by_complexity"].values()
        )
        
        # Calculate distribution
        distribution = {}
        total = self.stats["total_routes"]
        if total > 0:
            for complexity, data in self.stats["by_complexity"].items():
                distribution[complexity.value] = {
                    "count": data["count"],
                    "percentage": round(data["count"] / total * 100, 1),
                    "cost": round(data["cost"], 4)
                }
        
        return {
            "total_routes": self.stats["total_routes"],
            "total_cost": round(total_cost, 4),
            "cost_savings": round(self.stats["cost_savings"], 4),
            "escalations": self.stats["escalations"],
            "distribution": distribution,
            "target_80_20": "80% simple tasks → cheap models"
        }
    
    def print_report(self):
        """Print routing statistics report."""
        stats = self.get_stats()
        
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║           Smart Router Statistics                         ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"\nTotal Routes: {stats['total_routes']}")
        print(f"Total Cost: ${stats['total_cost']:.4f}")
        print(f"Cost Savings: ${stats['cost_savings']:.4f}")
        print(f"Escalations: {stats['escalations']}")
        
        print("\nComplexity Distribution:")
        for complexity, data in stats['distribution'].items():
            print(f"  {complexity}: {data['count']} ({data['percentage']}%) - ${data['cost']:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Testing OpenClaw Smart Router v3...\n")
    
    router = SmartRouter()
    
    # Mock LLM caller for testing
    def mock_llm_caller(model: str, prompt: str) -> Tuple[str, int, int]:
        """Simulate LLM call."""
        time.sleep(0.05)  # Simulate latency
        input_tokens = len(prompt) // 4
        output_tokens = input_tokens // 2
        return f"<Output from {model}>", input_tokens, output_tokens
    
    # Test 1: Simple task
    print("1. Simple Task (summarize):")
    result1 = router.execute_with_fallback(
        task_type="summarize_short",
        prompt="Summarize this in 3 bullet points: AI is transforming...",
        llm_caller=mock_llm_caller
    )
    print(f"   Model: {result1.model_used}")
    print(f"   Cost: ${result1.actual_cost:.6f}")
    
    # Test 2: Complex task
    print("\n2. Complex Task (architecture):")
    result2 = router.execute_with_fallback(
        task_type="architecture_design",
        prompt="Design a scalable microservices architecture for a fintech platform...",
        llm_caller=mock_llm_caller
    )
    print(f"   Model: {result2.model_used}")
    print(f"   Cost: ${result2.actual_cost:.6f}")
    
    # Test 3: Unknown task (auto-detected)
    print("\n3. Auto-detected Task:")
    decision = router.route(
        task_type="unknown_task",
        prompt="Extract keywords from this text and format as JSON"
    )
    print(f"   Detected: {decision.complexity.value}")
    print(f"   Routed to: {decision.model}")
    print(f"   Reason: {decision.reason}")
    
    # Print final report
    router.print_report()
    
    print("\n✅ Smart Router test complete!")