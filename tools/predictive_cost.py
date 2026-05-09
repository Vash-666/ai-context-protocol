#!/usr/bin/env python3
"""
OpenClaw Predictive Cost Modeling (Phase 3)
=============================================
Cost and latency prediction before execution.

Grok: "Predictive cost + latency modeling before execution."

Features:
- Pre-execution cost estimation
- Latency prediction
- Budget enforcement
- What-if analysis
- Cost optimization suggestions
- Historical pattern learning

Usage:
    from predictive_cost import CostPredictor
    
    predictor = CostPredictor()
    
    # Predict before executing
    prediction = predictor.predict(
        task_type="website_build",
        prompt_length=1500,
        complexity="moderate"
    )
    
    print(f"Estimated cost: ${prediction.cost_usd:.4f}")
    print(f"Estimated latency: {prediction.latency_ms:.0f}ms")
    
    # Check if within budget
    if predictor.is_within_budget(prediction, daily_budget=10.0):
        execute_task()
"""

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Import core components
try:
    from execution_tracer import tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

try:
    from state_kernel import StateKernel
    STATE_AVAILABLE = True
except ImportError:
    STATE_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
COST_MODEL_FILE = Path.home() / ".openclaw" / "workspace" / "cost_model.json"

# Model pricing (per 1K tokens)
MODEL_PRICING = {
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003, "latency_factor": 0.8},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005, "latency_factor": 1.0},
    "claude-sonnet-4-5": {"input": 0.003, "output": 0.015, "latency_factor": 1.5},
    "claude-opus-4": {"input": 0.015, "output": 0.075, "latency_factor": 2.5},
}

# Historical data retention
HISTORY_DAYS = 30

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class CostPrediction:
    """Cost and latency prediction."""
    task_type: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cost_range: Tuple[float, float]  # (min, max)
    latency_ms: float
    latency_range: Tuple[float, float]
    confidence: float  # 0-1
    factors: Dict[str, float]


@dataclass
class HistoricalData:
    """Historical execution data point."""
    task_type: str
    model: str
    input_tokens: int
    output_tokens: int
    actual_cost: float
    actual_latency: float
    timestamp: str
    success: bool


@dataclass
class BudgetStatus:
    """Current budget status."""
    daily_budget: float
    spent_today: float
    remaining_today: float
    projected_daily: float
    days_until_depletion: Optional[float]
    alert_level: str  # green, yellow, red


# ─────────────────────────────────────────────────────────────────────────────
# Cost Predictor
# ─────────────────────────────────────────────────────────────────────────────
class CostPredictor:
    """
    Predictive cost and latency modeling.
    
    Uses historical data and heuristics to estimate costs
    before task execution.
    """
    
    def __init__(self):
        self.history: List[HistoricalData] = []
        self.task_patterns: Dict[str, Dict] = defaultdict(lambda: {
            "token_ratio": 0.5,  # output/input ratio
            "avg_latency_per_token": 0.5,  # ms per token
            "success_rate": 0.95
        })
        self.daily_spending: Dict[str, float] = defaultdict(float)
        
        self._load_history()
        self._learn_patterns()
    
    def _load_history(self):
        """Load historical execution data."""
        if COST_MODEL_FILE.exists():
            with open(COST_MODEL_FILE, "r") as f:
                data = json.load(f)
                for item in data.get("history", []):
                    self.history.append(HistoricalData(**item))
        
        # Clean old data
        cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
        self.history = [
            h for h in self.history
            if datetime.fromisoformat(h.timestamp.replace('Z', '+00:00')) > cutoff
        ]
    
    def _save_history(self):
        """Save historical data."""
        data = {
            "history": [h.__dict__ for h in self.history],
            "patterns": dict(self.task_patterns)
        }
        with open(COST_MODEL_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _learn_patterns(self):
        """Learn patterns from historical data."""
        if not self.history:
            return
        
        # Group by task type
        by_task = defaultdict(list)
        for h in self.history:
            by_task[h.task_type].append(h)
        
        # Calculate patterns
        for task_type, executions in by_task.items():
            if len(executions) < 3:
                continue
            
            # Token ratio (output/input)
            ratios = [h.output_tokens / h.input_tokens if h.input_tokens > 0 else 0.5 
                      for h in executions]
            avg_ratio = statistics.median(ratios)
            
            # Latency per token
            latencies = [h.actual_latency / (h.input_tokens + h.output_tokens) 
                         if (h.input_tokens + h.output_tokens) > 0 else 0.5
                         for h in executions]
            avg_latency = statistics.median(latencies)
            
            # Success rate
            successes = sum(1 for h in executions if h.success)
            success_rate = successes / len(executions)
            
            self.task_patterns[task_type] = {
                "token_ratio": avg_ratio,
                "avg_latency_per_token": avg_latency,
                "success_rate": success_rate,
                "sample_size": len(executions)
            }
    
    def predict(
        self,
        task_type: str,
        model: str,
        input_tokens: int,
        use_historical: bool = True
    ) -> CostPrediction:
        """
        Predict cost and latency for a task.
        
        Args:
            task_type: Type of task (e.g., "website_build")
            model: Model to use
            input_tokens: Expected input token count
            use_historical: Whether to use historical patterns
        
        Returns:
            CostPrediction with estimates
        """
        # Get pricing
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-1.5-pro"])
        
        # Estimate output tokens
        if use_historical and task_type in self.task_patterns:
            pattern = self.task_patterns[task_type]
            token_ratio = pattern["token_ratio"]
            confidence = min(pattern["sample_size"] / 10, 1.0)  # Higher confidence with more data
        else:
            token_ratio = 0.5  # Default 50% output/input
            confidence = 0.5
        
        output_tokens = int(input_tokens * token_ratio)
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        estimated_cost = input_cost + output_cost
        
        # Cost range (±30% uncertainty)
        cost_min = estimated_cost * 0.7
        cost_max = estimated_cost * 1.3
        
        # Estimate latency
        if use_historical and task_type in self.task_patterns:
            latency_per_token = self.task_patterns[task_type]["avg_latency_per_token"]
        else:
            latency_per_token = pricing["latency_factor"] * 0.5
        
        total_tokens = input_tokens + output_tokens
        estimated_latency = total_tokens * latency_per_token
        
        # Latency range (±50% for network/model variance)
        latency_min = estimated_latency * 0.5
        latency_max = estimated_latency * 1.5
        
        prediction = CostPrediction(
            task_type=task_type,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=estimated_cost,
            cost_range=(cost_min, cost_max),
            latency_ms=estimated_latency,
            latency_range=(latency_min, latency_max),
            confidence=confidence,
            factors={
                "token_ratio": token_ratio,
                "latency_per_token": latency_per_token,
                "pricing_input": pricing["input"],
                "pricing_output": pricing["output"]
            }
        )
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="cost_prediction",
                agent="cost_predictor",
                step=task_type,
                metadata={
                    "model": model,
                    "estimated_cost": estimated_cost,
                    "estimated_latency": estimated_latency,
                    "confidence": confidence
                }
            )
        
        return prediction
    
    def predict_from_prompt(
        self,
        task_type: str,
        prompt: str,
        model: str = "gemini-1.5-pro"
    ) -> CostPrediction:
        """
        Predict cost from raw prompt.
        
        Estimates token count from prompt length.
        """
        # Rough estimate: 4 characters ≈ 1 token
        input_tokens = len(prompt) // 4
        
        return self.predict(task_type, model, input_tokens)
    
    def is_within_budget(
        self,
        prediction: CostPrediction,
        daily_budget: float = 10.0,
        safety_margin: float = 0.1
    ) -> bool:
        """
        Check if predicted cost is within budget.
        
        Args:
            prediction: Cost prediction
            daily_budget: Daily spending limit
            safety_margin: Extra buffer (0.1 = 10%)
        
        Returns:
            True if within budget
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        spent_today = self.daily_spending.get(today, 0)
        
        max_cost = prediction.cost_range[1]  # Use upper bound
        available = daily_budget * (1 - safety_margin) - spent_today
        
        return max_cost <= available
    
    def check_budget_status(self, daily_budget: float = 10.0) -> BudgetStatus:
        """Get current budget status."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        spent_today = self.daily_spending.get(today, 0)
        remaining = daily_budget - spent_today
        
        # Calculate projected daily spend based on history
        recent_days = list(self.daily_spending.keys())[-7:]
        if recent_days:
            avg_daily = sum(self.daily_spending.get(d, 0) for d in recent_days) / len(recent_days)
        else:
            avg_daily = spent_today
        
        # Days until depletion
        if avg_daily > 0:
            days_until = remaining / avg_daily
        else:
            days_until = None
        
        # Alert level
        utilization = spent_today / daily_budget if daily_budget > 0 else 0
        if utilization > 0.9:
            alert_level = "red"
        elif utilization > 0.7:
            alert_level = "yellow"
        else:
            alert_level = "green"
        
        return BudgetStatus(
            daily_budget=daily_budget,
            spent_today=spent_today,
            remaining_today=remaining,
            projected_daily=avg_daily,
            days_until_depletion=days_until,
            alert_level=alert_level
        )
    
    def record_actual(
        self,
        task_type: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        actual_cost: float,
        actual_latency: float,
        success: bool
    ):
        """Record actual execution data for future predictions."""
        data = HistoricalData(
            task_type=task_type,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            actual_cost=actual_cost,
            actual_latency=actual_latency,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=success
        )
        
        self.history.append(data)
        
        # Update daily spending
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.daily_spending[today] += actual_cost
        
        # Re-learn patterns
        self._learn_patterns()
        self._save_history()
    
    def compare_models(
        self,
        task_type: str,
        input_tokens: int
    ) -> List[Dict[str, Any]]:
        """Compare cost/latency across all models."""
        comparisons = []
        
        for model, pricing in MODEL_PRICING.items():
            prediction = self.predict(task_type, model, input_tokens)
            
            comparisons.append({
                "model": model,
                "cost_usd": prediction.cost_usd,
                "latency_ms": prediction.latency_ms,
                "confidence": prediction.confidence,
                "recommendation": self._get_model_recommendation(prediction)
            })
        
        # Sort by cost
        comparisons.sort(key=lambda x: x["cost_usd"])
        
        return comparisons
    
    def _get_model_recommendation(self, prediction: CostPrediction) -> str:
        """Generate recommendation for a model choice."""
        if prediction.cost_usd < 0.01:
            return "Most cost-effective"
        elif prediction.latency_ms < 1000:
            return "Fastest response"
        elif prediction.confidence > 0.8:
            return "Reliable prediction"
        else:
            return "Consider alternatives"
    
    def what_if_analysis(
        self,
        task_type: str,
        input_tokens: int,
        scenarios: List[Dict[str, Any]]
    ) -> List[CostPrediction]:
        """
        Run what-if analysis with different scenarios.
        
        Args:
            scenarios: List of scenario dicts with model, token_multiplier, etc.
        
        Returns:
            List of predictions for each scenario
        """
        results = []
        
        for scenario in scenarios:
            model = scenario.get("model", "gemini-1.5-pro")
            multiplier = scenario.get("token_multiplier", 1.0)
            
            adjusted_tokens = int(input_tokens * multiplier)
            prediction = self.predict(task_type, model, adjusted_tokens)
            
            results.append(prediction)
        
        return results
    
    def get_optimization_suggestions(
        self,
        prediction: CostPrediction
    ) -> List[str]:
        """Get suggestions to reduce cost/latency."""
        suggestions = []
        
        # Check if cheaper model could be used
        if prediction.model in ["claude-opus-4", "claude-sonnet-4-5"]:
            suggestions.append(
                f"Consider using gemini-1.5-pro for potential "
                f"{(MODEL_PRICING[prediction.model]['output'] / MODEL_PRICING['gemini-1.5-pro']['output']):.1f}x cost savings"
            )
        
        # Check prompt length
        if prediction.input_tokens > 4000:
            suggestions.append(
                "Long prompt detected. Consider chunking or summarization to reduce token count"
            )
        
        # Check latency
        if prediction.latency_ms > 5000:
            suggestions.append(
                "High latency predicted. Consider using faster model or caching"
            )
        
        # Check confidence
        if prediction.confidence < 0.7:
            suggestions.append(
                "Low confidence prediction. Limited historical data for this task type"
            )
        
        return suggestions


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("💰 Testing OpenClaw Predictive Cost Modeling...\n")
    
    predictor = CostPredictor()
    
    print("1. Predicting cost for website build...")
    
    prediction = predictor.predict(
        task_type="website_build",
        model="gemini-1.5-pro",
        input_tokens=1500
    )
    
    print(f"   Task: {prediction.task_type}")
    print(f"   Model: {prediction.model}")
    print(f"   Input tokens: {prediction.input_tokens}")
    print(f"   Output tokens (est): {prediction.output_tokens}")
    print(f"   Cost: ${prediction.cost_usd:.6f}")
    print(f"   Cost range: ${prediction.cost_range[0]:.6f} - ${prediction.cost_range[1]:.6f}")
    print(f"   Latency: {prediction.latency_ms:.0f}ms")
    print(f"   Confidence: {prediction.confidence:.0%}")
    
    print("\n2. Predicting from prompt...")
    
    prompt = "Build a responsive landing page with hero section, features grid, and contact form"
    prompt_prediction = predictor.predict_from_prompt(
        task_type="website_build",
        prompt=prompt
    )
    
    print(f"   Prompt length: {len(prompt)} chars")
    print(f"   Estimated tokens: {prompt_prediction.input_tokens}")
    print(f"   Estimated cost: ${prompt_prediction.cost_usd:.6f}")
    
    print("\n3. Checking budget status...")
    
    budget = predictor.check_budget_status(daily_budget=10.0)
    print(f"   Daily budget: ${budget.daily_budget:.2f}")
    print(f"   Spent today: ${budget.spent_today:.4f}")
    print(f"   Remaining: ${budget.remaining_today:.2f}")
    print(f"   Alert level: {budget.alert_level}")
    
    print("\n4. Within budget check...")
    
    within_budget = predictor.is_within_budget(prediction, daily_budget=10.0)
    print(f"   Within budget: {within_budget}")
    
    print("\n5. Model comparison...")
    
    comparisons = predictor.compare_models("website_build", 1500)
    print(f"   Model options (sorted by cost):")
    for comp in comparisons:
        print(f"     {comp['model']}: ${comp['cost_usd']:.6f}, {comp['latency_ms']:.0f}ms")
    
    print("\n6. Optimization suggestions...")
    
    suggestions = predictor.get_optimization_suggestions(prediction)
    for suggestion in suggestions:
        print(f"   - {suggestion}")
    
    print("\n7. Recording actual data...")
    
    predictor.record_actual(
        task_type="website_build",
        model="gemini-1.5-pro",
        input_tokens=1500,
        output_tokens=800,
        actual_cost=0.0085,
        actual_latency=2300,
        success=True
    )
    
    print("   Recorded for future predictions")
    
    print("\n✅ Predictive Cost Modeling test complete!")
    print("   Model file:", COST_MODEL_FILE)


if __name__ == "__main__":
    main()
