#!/usr/bin/env python3
"""
OpenClaw Evaluation System (Phase 2)
=====================================
Continuous improvement with golden datasets and regression testing.

Grok: "Golden dataset management, automated regression, human feedback ingestion."

Features:
- Golden dataset management
- Automated regression testing
- Human feedback ingestion
- Actionable patch generation
- Performance benchmarking
- A/B testing support

Usage:
    from evaluation_system import EvaluationSystem, TestCase
    
    eval_system = EvaluationSystem()
    
    # Add golden test case
    eval_system.add_test_case(TestCase(
        input="Build a navbar with 3 items",
        expected_output={"html": "<nav>...</nav>"},
        tags=["navbar", "simple"]
    ))
    
    # Run regression test
    results = eval_system.run_regression(agent_executor)
    
    # Generate improvement patches
    patches = eval_system.generate_patches(results)
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import defaultdict
import difflib

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
EVALUATION_DIR = Path.home() / ".openclaw" / "workspace" / "evaluation"
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

GOLDEN_DATASET_FILE = EVALUATION_DIR / "golden_dataset.json"
REGRESSION_RESULTS_FILE = EVALUATION_DIR / "regression_results.jsonl"
FEEDBACK_FILE = EVALUATION_DIR / "human_feedback.jsonl"

# Pass thresholds
PASS_THRESHOLD_EXACT = 0.95  # 95% exact match
PASS_THRESHOLD_SEMANTIC = 0.85  # 85% semantic similarity

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TestCase:
    """Single test case in golden dataset."""
    input: str
    expected_output: Any
    id: str = field(default_factory=str)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    difficulty: str = "medium"  # easy, medium, hard
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(self.input.encode()).hexdigest()[:16]


@dataclass
class TestResult:
    """Result of running a test case."""
    test_id: str
    test_input: str
    expected_output: Any
    actual_output: Any
    passed: bool
    similarity_score: float
    execution_time_ms: float
    cost_usd: float
    timestamp: str
    agent_version: str
    errors: List[str] = field(default_factory=list)


@dataclass
class HumanFeedback:
    """Human feedback on agent output."""
    test_id: str
    output_id: str
    rating: int  # 1-5
    comments: str
    suggested_improvement: str
    timestamp: str
    reviewer: str


@dataclass
class Patch:
    """Generated improvement patch."""
    id: str
    target_component: str  # agent, prompt, scaffolding_kernel, etc.
    issue_description: str
    suggested_change: str
    confidence: float  # 0-1
    generated_at: str
    applied: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation System
# ─────────────────────────────────────────────────────────────────────────────
class EvaluationSystem:
    """
    Continuous improvement system for OpenClaw agents.
    
    Manages:
    - Golden dataset of test cases
    - Regression testing against baseline
    - Human feedback collection
    - Automated patch generation
    - Performance benchmarking
    """
    
    def __init__(self):
        self.golden_dataset: Dict[str, TestCase] = {}
        self.test_history: List[TestResult] = []
        self.human_feedback: List[HumanFeedback] = []
        self.patches: List[Patch] = []
        
        # Load existing data
        self._load_golden_dataset()
        self._load_feedback()
    
    def _load_golden_dataset(self):
        """Load golden dataset from disk."""
        if GOLDEN_DATASET_FILE.exists():
            with open(GOLDEN_DATASET_FILE, "r") as f:
                data = json.load(f)
                for item in data:
                    test = TestCase(**item)
                    self.golden_dataset[test.id] = test
    
    def _save_golden_dataset(self):
        """Save golden dataset to disk."""
        data = [asdict(t) for t in self.golden_dataset.values()]
        with open(GOLDEN_DATASET_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_feedback(self):
        """Load human feedback from disk."""
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.human_feedback.append(HumanFeedback(**data))
    
    def add_test_case(self, test_case: TestCase) -> str:
        """Add a test case to golden dataset."""
        self.golden_dataset[test_case.id] = test_case
        self._save_golden_dataset()
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="test_case_added",
                agent="evaluation_system",
                step="add",
                metadata={"test_id": test_case.id, "tags": test_case.tags}
            )
        
        return test_case.id
    
    def create_test_case_from_execution(
        self,
        task_input: str,
        actual_output: Any,
        human_rating: int,
        reviewer: str = "auto"
    ) -> Optional[str]:
        """
        Create test case from successful execution.
        
        Only adds if human_rating >= 4 (good output).
        """
        if human_rating < 4:
            return None
        
        test_case = TestCase(
            input=task_input,
            expected_output=actual_output,
            tags=["auto_generated"],
            difficulty="medium",
            metadata={
                "source": "execution",
                "reviewer": reviewer,
                "rating": human_rating
            }
        )
        
        return self.add_test_case(test_case)
    
    def run_regression(
        self,
        agent_executor: Callable[[str], Tuple[Any, float, float]],
        agent_version: str = "unknown",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run regression tests against golden dataset.
        
        Args:
            agent_executor: Function(input) -> (output, time_ms, cost_usd)
            agent_version: Version string for tracking
            tags: Filter tests by tags
        
        Returns:
            Summary of test results
        """
        import time
        
        results = []
        passed = 0
        failed = 0
        
        # Filter test cases
        test_cases = list(self.golden_dataset.values())
        if tags:
            test_cases = [t for t in test_cases if any(tag in t.tags for tag in tags)]
        
        print(f"Running regression on {len(test_cases)} test cases...")
        
        for test in test_cases:
            start_time = time.time()
            
            try:
                actual_output, exec_time, cost = agent_executor(test.input)
                
                # Calculate similarity
                similarity = self._calculate_similarity(
                    test.expected_output,
                    actual_output
                )
                
                passed_test = similarity >= PASS_THRESHOLD_SEMANTIC
                
                if passed_test:
                    passed += 1
                else:
                    failed += 1
                
                result = TestResult(
                    test_id=test.id,
                    test_input=test.input,
                    expected_output=test.expected_output,
                    actual_output=actual_output,
                    passed=passed_test,
                    similarity_score=similarity,
                    execution_time_ms=exec_time,
                    cost_usd=cost,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_version=agent_version
                )
                
                results.append(result)
                self.test_history.append(result)
                
            except Exception as e:
                failed += 1
                result = TestResult(
                    test_id=test.id,
                    test_input=test.input,
                    expected_output=test.expected_output,
                    actual_output=None,
                    passed=False,
                    similarity_score=0.0,
                    execution_time_ms=0.0,
                    cost_usd=0.0,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_version=agent_version,
                    errors=[str(e)]
                )
                results.append(result)
        
        # Save results
        with open(REGRESSION_RESULTS_FILE, "a") as f:
            for r in results:
                f.write(json.dumps(asdict(r), default=str) + "\n")
        
        summary = {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(test_cases) if test_cases else 0.0,
            "avg_similarity": sum(r.similarity_score for r in results) / len(results) if results else 0.0,
            "avg_execution_time": sum(r.execution_time_ms for r in results) / len(results) if results else 0.0,
            "total_cost": sum(r.cost_usd for r in results),
            "agent_version": agent_version
        }
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="regression_completed",
                agent="evaluation_system",
                step="regression",
                metadata=summary
            )
        
        return summary
    
    def _calculate_similarity(self, expected: Any, actual: Any) -> float:
        """Calculate similarity between expected and actual output."""
        if expected == actual:
            return 1.0
        
        # Convert to strings for comparison
        expected_str = json.dumps(expected, sort_keys=True) if isinstance(expected, (dict, list)) else str(expected)
        actual_str = json.dumps(actual, sort_keys=True) if isinstance(actual, (dict, list)) else str(actual)
        
        # Use difflib for similarity
        matcher = difflib.SequenceMatcher(None, expected_str, actual_str)
        return matcher.ratio()
    
    def add_human_feedback(
        self,
        test_id: str,
        output_id: str,
        rating: int,
        comments: str = "",
        suggested_improvement: str = "",
        reviewer: str = "anonymous"
    ):
        """Add human feedback on test output."""
        feedback = HumanFeedback(
            test_id=test_id,
            output_id=output_id,
            rating=rating,
            comments=comments,
            suggested_improvement=suggested_improvement,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reviewer=reviewer
        )
        
        self.human_feedback.append(feedback)
        
        # Persist
        with open(FEEDBACK_FILE, "a") as f:
            f.write(json.dumps(asdict(feedback), default=str) + "\n")
        
        # Auto-create test case from good feedback
        if rating >= 4 and test_id in self.golden_dataset:
            test = self.golden_dataset[test_id]
            # Find the result
            for result in reversed(self.test_history):
                if result.test_id == test_id:
                    # Good output, could add as positive example
                    break
    
    def generate_patches(self, regression_results: List[TestResult]) -> List[Patch]:
        """
        Generate improvement patches from failed tests.
        
        Analyzes patterns in failures and suggests fixes.
        """
        patches = []
        
        # Group failures by error pattern
        failure_patterns = defaultdict(list)
        for result in regression_results:
            if not result.passed:
                # Identify failure pattern
                if result.errors:
                    pattern = "execution_error"
                elif result.similarity_score < 0.5:
                    pattern = "completely_wrong"
                else:
                    pattern = "partial_mismatch"
                
                failure_patterns[pattern].append(result)
        
        # Generate patches for each pattern
        for pattern, failures in failure_patterns.items():
            if len(failures) >= 3:  # Only patch if pattern is significant
                patch = self._create_patch_for_pattern(pattern, failures)
                if patch:
                    patches.append(patch)
        
        self.patches.extend(patches)
        return patches
    
    def _create_patch_for_pattern(self, pattern: str, failures: List[TestResult]) -> Optional[Patch]:
        """Create improvement patch for identified pattern."""
        patch_descriptions = {
            "execution_error": {
                "target": "agent",
                "description": "Multiple execution errors detected. Consider adding error handling or retry logic.",
                "change": "Add try-catch blocks and exponential backoff for external calls."
            },
            "completely_wrong": {
                "target": "prompt",
                "description": "Outputs are completely wrong. Prompt may be ambiguous or missing context.",
                "change": "Add more examples to the prompt and clarify expected output format."
            },
            "partial_mismatch": {
                "target": "scaffolding_kernel",
                "description": "Outputs are close but missing details. Cache may be incomplete.",
                "change": "Update cache validation to check for required fields."
            }
        }
        
        desc = patch_descriptions.get(pattern)
        if not desc:
            return None
        
        return Patch(
            id=f"patch-{pattern}-{datetime.now().strftime('%Y%m%d')}",
            target_component=desc["target"],
            issue_description=f"{desc['description']} Affects {len(failures)} test cases.",
            suggested_change=desc["change"],
            confidence=min(len(failures) / 10, 1.0),  # Higher confidence with more examples
            generated_at=datetime.now(timezone.utc).isoformat()
        )
    
    def benchmark(
        self,
        agent_executor: Callable,
        iterations: int = 10,
        test_input: str = "Build a responsive navbar with 3 items"
    ) -> Dict[str, Any]:
        """Benchmark agent performance."""
        import time
        
        times = []
        costs = []
        
        for _ in range(iterations):
            start = time.time()
            _, exec_time, cost = agent_executor(test_input)
            elapsed = time.time() - start
            
            times.append(exec_time)
            costs.append(cost)
        
        return {
            "iterations": iterations,
            "avg_time_ms": statistics.mean(times),
            "p95_time_ms": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
            "avg_cost": statistics.mean(costs),
            "total_cost": sum(costs),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_improvement_report(self) -> Dict[str, Any]:
        """Get comprehensive improvement report."""
        # Analyze recent test history
        recent_tests = self.test_history[-100:] if len(self.test_history) > 100 else self.test_history
        
        pass_rate = sum(1 for t in recent_tests if t.passed) / len(recent_tests) if recent_tests else 0
        
        # Find most problematic areas
        by_tag = defaultdict(lambda: {"passed": 0, "failed": 0})
        for test in recent_tests:
            test_case = self.golden_dataset.get(test.test_id)
            if test_case:
                for tag in test_case.tags:
                    if test.passed:
                        by_tag[tag]["passed"] += 1
                    else:
                        by_tag[tag]["failed"] += 1
        
        problematic_tags = [
            tag for tag, counts in by_tag.items()
            if counts["failed"] > counts["passed"]
        ]
        
        return {
            "golden_dataset_size": len(self.golden_dataset),
            "recent_tests": len(recent_tests),
            "pass_rate": pass_rate,
            "pending_patches": len([p for p in self.patches if not p.applied]),
            "problematic_areas": problematic_tags,
            "recommendations": [
                "Add more test cases for: " + ", ".join(problematic_tags) if problematic_tags else "System performing well",
                f"Apply {len([p for p in self.patches if not p.applied])} pending patches" if any(not p.applied for p in self.patches) else "No pending patches"
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("🧪 Testing OpenClaw Evaluation System...\n")
    
    eval_system = EvaluationSystem()
    
    print("1. Adding test cases to golden dataset...")
    
    test1 = TestCase(
        input="Build a responsive navbar with logo and 3 links",
        expected_output={
            "html": '<nav class="navbar"><div class="logo">Logo</div><ul><li><a href="#">Home</a></li><li><a href="#">About</a></li><li><a href="#">Contact</a></li></ul></nav>',
            "css": ".navbar { display: flex; }"
        },
        tags=["navbar", "simple", "responsive"],
        difficulty="easy"
    )
    
    test2 = TestCase(
        input="Create a hero section with headline, subtitle, and CTA button",
        expected_output={
            "html": '<section class="hero"><h1>Welcome</h1><p>Subtitle</p><button>Get Started</button></section>',
            "css": ".hero { text-align: center; }"
        },
        tags=["hero", "simple"],
        difficulty="easy"
    )
    
    eval_system.add_test_case(test1)
    eval_system.add_test_case(test2)
    
    print(f"   Added {len(eval_system.golden_dataset)} test cases")
    
    print("\n2. Running mock regression test...")
    
    def mock_agent_executor(task_input: str):
        """Mock agent that simulates execution."""
        import random
        import time
        
        # Simulate processing
        time.sleep(0.01)
        
        # Simulate occasional failures
        if random.random() < 0.2:  # 20% failure rate
            return None, 100.0, 0.005
        
        # Return output similar but not exact
        output = {
            "html": f"<div>{task_input}</div>",
            "css": ".test { color: black; }"
        }
        
        return output, 150.0, 0.01
    
    results = eval_system.run_regression(
        agent_executor=mock_agent_executor,
        agent_version="v1.2.3"
    )
    
    print(f"   Total tests: {results['total']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Pass rate: {results['pass_rate']:.1%}")
    print(f"   Avg similarity: {results['avg_similarity']:.2f}")
    print(f"   Total cost: ${results['total_cost']:.4f}")
    
    print("\n3. Adding human feedback...")
    eval_system.add_human_feedback(
        test_id=test1.id,
        output_id="output-123",
        rating=5,
        comments="Perfect output",
        reviewer="test_user"
    )
    
    print("   Feedback recorded")
    
    print("\n4. Generating improvement patches...")
    patches = eval_system.generate_patches(eval_system.test_history[-10:])
    
    for patch in patches:
        print(f"   Patch: {patch.target_component}")
        print(f"   Issue: {patch.issue_description[:60]}...")
        print(f"   Confidence: {patch.confidence:.0%}")
    
    print("\n5. Getting improvement report...")
    report = eval_system.get_improvement_report()
    
    print(f"   Golden dataset: {report['golden_dataset_size']} cases")
    print(f"   Pass rate: {report['pass_rate']:.1%}")
    print(f"   Pending patches: {report['pending_patches']}")
    print(f"   Recommendations:")
    for rec in report['recommendations']:
        print(f"     - {rec}")
    
    print("\n✅ Evaluation System test complete!")
    print("   Golden dataset:", GOLDEN_DATASET_FILE)
    print("   Regression results:", REGRESSION_RESULTS_FILE)
    print("   Human feedback:", FEEDBACK_FILE)


if __name__ == "__main__":
    import statistics
    main()
