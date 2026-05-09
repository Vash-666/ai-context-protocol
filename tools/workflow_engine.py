#!/usr/bin/env python3
"""
OpenClaw Workflow Engine (Phase 2)
===================================
Control plane with DAG-based workflows, compensation logic, and saga patterns.
Replaces ad-hoc agent spawning with declarative, observable orchestration.

Grok: "Make multi-agent coordination explicit and observable."

Features:
- DAG-based workflow definitions
- Automatic parallelization where safe
- Compensation logic (rollback on failure)
- Saga pattern for distributed transactions
- Integration with State Kernel for durability
- Integration with Shield for safety

Usage:
    from workflow_engine import WorkflowEngine, Task
    
    engine = WorkflowEngine()
    
    # Define workflow
    workflow = {
        "tasks": [
            Task(id="research", agent="quality", action="analyze_requirements"),
            Task(id="design", agent="scaffolder", action="create_architecture", depends_on=["research"]),
            Task(id="build", agent="website_builder", action="generate_code", depends_on=["design"]),
            Task(id="test", agent="quality", action="validate", depends_on=["build"]),
        ]
    }
    
    # Execute with automatic parallelization and rollback
    result = engine.execute(workflow, workflow_id="wf-123")
"""

import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

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

try:
    from shield import Shield, PermissionLevel
    SHIELD_AVAILABLE = True
except ImportError:
    SHIELD_AVAILABLE = False

try:
    from task_queue import submit_task, get_result
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class Task:
    """A task in the workflow DAG."""
    id: str
    agent: str
    action: str
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    compensation_action: Optional[str] = None
    compensation_args: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 2
    timeout_seconds: int = 300
    required_permission: PermissionLevel = PermissionLevel.WRITE_SAFE if SHIELD_AVAILABLE else None
    
    # Runtime fields
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    task_id: Optional[str] = None  # External task queue ID


@dataclass
class Workflow:
    """Workflow definition with DAG of tasks."""
    id: str
    tasks: List[Task]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Runtime state
    status: str = "pending"
    current_tasks: Set[str] = field(default_factory=set)
    completed_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    success: bool
    tasks_completed: int
    tasks_failed: int
    results: Dict[str, Any]
    errors: Dict[str, str]
    duration_seconds: float
    compensated_tasks: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Workflow Engine
# ─────────────────────────────────────────────────────────────────────────────
class WorkflowEngine:
    """
    Control plane for multi-agent workflows.
    
    Orchestrates task execution with:
    - DAG dependency resolution
    - Parallel execution where safe
    - Automatic compensation on failure
    - Saga pattern support
    """
    
    def __init__(self):
        self.state = StateKernel() if STATE_AVAILABLE else None
        self.shield = Shield() if SHIELD_AVAILABLE else None
        self.active_workflows: Dict[str, Workflow] = {}
        self.task_executors: Dict[str, Callable] = {}
        
        # Register default executors
        self._register_default_executors()
    
    def _register_default_executors(self):
        """Register default task executors."""
        self.task_executors["default"] = self._default_executor
    
    def register_executor(self, action: str, executor: Callable):
        """Register a custom executor for an action type."""
        self.task_executors[action] = executor
    
    def create_workflow(self, tasks: List[Task], metadata: Optional[Dict] = None) -> str:
        """Create a new workflow with DAG of tasks."""
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        
        workflow = Workflow(
            id=workflow_id,
            tasks=tasks,
            metadata=metadata or {}
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Persist workflow creation
        if self.state:
            self.state.append_event(
                workflow_id=workflow_id,
                agent="workflow_engine",
                event_type="workflow_created",
                data={"task_count": len(tasks), "metadata": metadata}
            )
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="workflow_created",
                agent="workflow_engine",
                step="create",
                metadata={"workflow_id": workflow_id, "tasks": len(tasks)}
            )
        
        return workflow_id
    
    async def execute(self, workflow_id: str) -> WorkflowResult:
        """
        Execute workflow with automatic parallelization and compensation.
        
        This is the main entry point for workflow execution.
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        start_time = datetime.now(timezone.utc)
        workflow.status = "running"
        
        # Create checkpoint before execution
        if self.state:
            checkpoint_id = self.state.create_checkpoint(
                workflow_id=workflow_id,
                state_snapshot={"tasks": [t.id for t in workflow.tasks]}
            )
        
        try:
            # Execute tasks in dependency order
            while workflow.completed_tasks | workflow.failed_tasks != set(t.id for t in workflow.tasks):
                # Find ready tasks (dependencies satisfied)
                ready_tasks = self._get_ready_tasks(workflow)
                
                if not ready_tasks and workflow.current_tasks:
                    # Wait for current tasks to complete
                    await asyncio.sleep(0.1)
                    continue
                
                if not ready_tasks and not workflow.current_tasks:
                    # Deadlock or all done
                    break
                
                # Execute ready tasks in parallel
                task_coros = [self._execute_task(workflow, task) for task in ready_tasks]
                await asyncio.gather(*task_coros, return_exceptions=True)
                
                # Check for failures that need compensation
                if workflow.failed_tasks:
                    await self._compensate_workflow(workflow)
                    break
            
            # Determine final status
            workflow.status = "completed" if not workflow.failed_tasks else "failed"
            
        except Exception as e:
            workflow.status = "failed"
            if TRACING_AVAILABLE:
                tracer.record_event(
                    event_type="workflow_error",
                    agent="workflow_engine",
                    step="execute",
                    error=str(e)
                )
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Build result
        result = WorkflowResult(
            workflow_id=workflow_id,
            success=workflow.status == "completed",
            tasks_completed=len(workflow.completed_tasks),
            tasks_failed=len(workflow.failed_tasks),
            results={t.id: t.result for t in workflow.tasks if t.status == TaskStatus.COMPLETED},
            errors={t.id: t.error for t in workflow.tasks if t.status == TaskStatus.FAILED},
            duration_seconds=duration,
            compensated_tasks=[t.id for t in workflow.tasks if t.status == TaskStatus.COMPENSATED]
        )
        
        # Persist completion
        if self.state:
            self.state.append_event(
                workflow_id=workflow_id,
                agent="workflow_engine",
                event_type="workflow_completed",
                data={
                    "success": result.success,
                    "tasks_completed": result.tasks_completed,
                    "duration": duration
                }
            )
        
        return result
    
    def _get_ready_tasks(self, workflow: Workflow) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in workflow.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            if task.id in workflow.current_tasks:
                continue
            
            # Check if dependencies are satisfied
            deps_satisfied = all(
                dep in workflow.completed_tasks 
                for dep in task.depends_on
            )
            
            if deps_satisfied:
                ready.append(task)
        
        return ready
    
    async def _execute_task(self, workflow: Workflow, task: Task):
        """Execute a single task with retry and compensation support."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        workflow.current_tasks.add(task.id)
        
        # Check permission with Shield
        if self.shield and task.required_permission:
            has_perm = self.shield.check_permission(task.agent, task.required_permission)
            if not has_perm:
                task.status = TaskStatus.FAILED
                task.error = f"Permission denied: {task.required_permission.value}"
                workflow.failed_tasks.add(task.id)
                workflow.current_tasks.discard(task.id)
                return
        
        # Get executor
        executor = self.task_executors.get(task.action, self.task_executors["default"])
        
        # Execute with retries
        for attempt in range(task.max_retries + 1):
            try:
                # Execute via task queue if available
                if QUEUE_AVAILABLE:
                    task.task_id = submit_task(
                        agent_name=task.agent,
                        func=lambda: executor(task.action, task.args),
                        timeout=task.timeout_seconds
                    )
                    
                    # Wait for completion
                    while True:
                        result = get_result(task.task_id, wait=True, timeout=1.0)
                        if result:
                            break
                        await asyncio.sleep(0.1)
                    
                    if result.get("status") == "completed":
                        task.result = result.get("result")
                        task.status = TaskStatus.COMPLETED
                    else:
                        raise Exception(result.get("error", "Unknown error"))
                else:
                    # Direct execution
                    task.result = await asyncio.wait_for(
                        asyncio.to_thread(executor, task.action, task.args),
                        timeout=task.timeout_seconds
                    )
                    task.status = TaskStatus.COMPLETED
                
                # Success - break retry loop
                break
                
            except Exception as e:
                task.retry_count += 1
                if task.retry_count > task.max_retries:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    workflow.failed_tasks.add(task.id)
                else:
                    # Retry after delay
                    await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
        
        task.completed_at = datetime.now(timezone.utc).isoformat()
        workflow.current_tasks.discard(task.id)
        
        if task.status == TaskStatus.COMPLETED:
            workflow.completed_tasks.add(task.id)
        
        # Persist task completion
        if self.state:
            self.state.append_event(
                workflow_id=workflow.id,
                agent=task.agent,
                event_type=f"task_{task.status.value}",
                data={"task_id": task.id, "action": task.action}
            )
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type=f"task_{task.status.value}",
                agent=task.agent,
                step=task.action,
                metadata={"task_id": task.id, "workflow_id": workflow.id}
            )
    
    async def _compensate_workflow(self, workflow: Workflow):
        """Execute compensation logic for failed workflow (Saga pattern)."""
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="compensation_started",
                agent="workflow_engine",
                step="compensate",
                metadata={"workflow_id": workflow.id}
            )
        
        # Find completed tasks that need compensation
        for task in reversed(workflow.tasks):
            if task.status != TaskStatus.COMPLETED:
                continue
            if not task.compensation_action:
                continue
            
            task.status = TaskStatus.COMPENSATING
            
            try:
                executor = self.task_executors.get(
                    task.compensation_action, 
                    self.task_executors["default"]
                )
                
                # Execute compensation
                if QUEUE_AVAILABLE:
                    comp_task_id = submit_task(
                        agent_name=task.agent,
                        func=lambda: executor(task.compensation_action, task.compensation_args),
                        timeout=60
                    )
                    result = get_result(comp_task_id, wait=True, timeout=65.0)
                    success = result.get("status") == "completed"
                else:
                    await asyncio.to_thread(
                        executor, 
                        task.compensation_action, 
                        task.compensation_args
                    )
                    success = True
                
                if success:
                    task.status = TaskStatus.COMPENSATED
                else:
                    task.error = "Compensation failed"
                    
            except Exception as e:
                task.error = f"Compensation error: {str(e)}"
    
    def _default_executor(self, action: str, args: Dict) -> Any:
        """Default task executor."""
        # In production, this would dispatch to actual agent implementations
        return {"action": action, "args": args, "status": "completed"}
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current status of a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "id": workflow.id,
            "status": workflow.status,
            "tasks_total": len(workflow.tasks),
            "tasks_completed": len(workflow.completed_tasks),
            "tasks_failed": len(workflow.failed_tasks),
            "tasks_running": len(workflow.current_tasks),
            "progress": len(workflow.completed_tasks) / len(workflow.tasks) * 100
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or workflow.status != "running":
            return False
        
        workflow.status = "cancelled"
        
        if self.state:
            self.state.append_event(
                workflow_id=workflow_id,
                agent="workflow_engine",
                event_type="workflow_cancelled",
                data={}
            )
        
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("🧪 Testing OpenClaw Workflow Engine...\n")
    
    engine = WorkflowEngine()
    
    # Define a workflow
    tasks = [
        Task(id="research", agent="quality", action="analyze_requirements", args={"project": "website"}),
        Task(
            id="design", 
            agent="scaffolder", 
            action="create_architecture", 
            depends_on=["research"],
            args={"style": "modern"}
        ),
        Task(
            id="build_frontend", 
            agent="website_builder", 
            action="generate_html", 
            depends_on=["design"],
            args={"pages": ["home", "about"]}
        ),
        Task(
            id="build_backend", 
            agent="scaffolder", 
            action="generate_api", 
            depends_on=["design"],
            args={"endpoints": ["users", "posts"]}
        ),
        Task(
            id="test", 
            agent="quality", 
            action="run_tests", 
            depends_on=["build_frontend", "build_backend"],
            compensation_action="revert_deployment"
        ),
    ]
    
    workflow_id = engine.create_workflow(tasks, metadata={"project": "ecommerce_site"})
    print(f"1. Created workflow: {workflow_id}")
    print(f"   Tasks: {len(tasks)}")
    
    # Execute workflow
    print("\n2. Executing workflow...")
    result = await engine.execute(workflow_id)
    
    print(f"\n3. Workflow completed:")
    print(f"   Success: {result.success}")
    print(f"   Tasks completed: {result.tasks_completed}")
    print(f"   Tasks failed: {result.tasks_failed}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    
    if result.compensated_tasks:
        print(f"   Compensated tasks: {result.compensated_tasks}")
    
    # Get final status
    status = engine.get_workflow_status(workflow_id)
    print(f"\n4. Final status:")
    print(f"   Progress: {status['progress']:.0f}%")
    
    print("\n✅ Workflow Engine test complete!")


if __name__ == "__main__":
    asyncio.run(main())
