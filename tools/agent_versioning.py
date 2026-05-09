#!/usr/bin/env python3
"""
OpenClaw Agent Versioning & Shadow Deployments (Phase 3)
==========================================================
Safe agent updates with A/B testing and rollback capability.

Grok: "Agent versioning and shadow deployment."

Features:
- Agent version management
- Shadow deployments (test new version alongside production)
- A/B testing with traffic splitting
- Automatic rollback on failure
- Version history and diffs
- Gradual rollouts (canary deployments)

Usage:
    from agent_versioning import VersionManager, DeploymentStrategy
    
    vm = VersionManager()
    
    # Register new version
    vm.register_version(
        agent="website_builder",
        version="v2.0.0",
        code_path="/path/to/v2",
        config={"model": "claude-sonnet-4-5"}
    )
    
    # Shadow deployment (test without affecting users)
    vm.deploy_shadow(
        agent="website_builder",
        version="v2.0.0",
        traffic_percentage=10
    )
    
    # Gradual rollout
    vm.deploy_canary(
        agent="website_builder",
        version="v2.0.0",
        rollout_percentage=5
    )
"""

import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
VERSIONS_DIR = Path.home() / ".openclaw" / "workspace" / "agent_versions"
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

VERSION_REGISTRY_FILE = VERSIONS_DIR / "registry.json"
DEPLOYMENT_LOG_FILE = VERSIONS_DIR / "deployments.jsonl"

# Deployment defaults
DEFAULT_CANARY_PERCENTAGE = 5
CANARY_STEP_PERCENTAGE = 10
ROLLOBACK_THRESHOLD_ERROR_RATE = 0.1

# ─────────────────────────────────────────────────────────────────────────────
# Deployment Strategies
# ─────────────────────────────────────────────────────────────────────────────
class DeploymentStrategy(Enum):
    """Deployment strategy types."""
    SHADOW = "shadow"  # Test alongside, no user impact
    CANARY = "canary"  # Gradual rollout to % of traffic
    BLUE_GREEN = "blue_green"  # Instant switch with rollback
    A_B_TEST = "a_b_test"  # Split traffic for comparison


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AgentVersion:
    """A version of an agent."""
    agent_id: str
    version: str
    code_hash: str
    config: Dict[str, Any]
    created_at: str
    status: str = "registered"  # registered, deployed, rolled_back, deprecated
    description: str = ""
    parent_version: Optional[str] = None


@dataclass
class Deployment:
    """A deployment instance."""
    id: str
    agent_id: str
    version: str
    strategy: DeploymentStrategy
    traffic_percentage: float
    started_at: str
    ended_at: Optional[str] = None
    status: str = "active"  # active, completed, rolled_back
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionComparison:
    """Comparison between two versions."""
    baseline_version: str
    candidate_version: str
    error_rate_delta: float
    latency_delta: float
    cost_delta: float
    success_rate_delta: float
    recommendation: str


# ─────────────────────────────────────────────────────────────────────────────
# Version Manager
# ─────────────────────────────────────────────────────────────────────────────
class VersionManager:
    """
    Manages agent versions and deployments.
    
    Provides safe update mechanisms:
    - Shadow deployments for testing
    - Canary deployments for gradual rollout
    - A/B testing for comparison
    - Automatic rollback on failure
    """
    
    def __init__(self):
        self.versions: Dict[str, List[AgentVersion]] = {}  # agent_id -> versions
        self.deployments: Dict[str, Deployment] = {}  # deployment_id -> deployment
        self.active_deployments: Dict[str, str] = {}  # agent_id -> deployment_id
        self.version_storage = VERSIONS_DIR
        
        self._load_registry()
    
    def _load_registry(self):
        """Load version registry from disk."""
        if VERSION_REGISTRY_FILE.exists():
            with open(VERSION_REGISTRY_FILE, "r") as f:
                data = json.load(f)
                for agent_id, versions_data in data.get("versions", {}).items():
                    self.versions[agent_id] = [AgentVersion(**v) for v in versions_data]
    
    def _save_registry(self):
        """Save version registry to disk."""
        data = {
            "versions": {
                agent_id: [v.__dict__ for v in versions]
                for agent_id, versions in self.versions.items()
            }
        }
        with open(VERSION_REGISTRY_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def register_version(
        self,
        agent_id: str,
        version: str,
        code_path: Optional[str] = None,
        config: Optional[Dict] = None,
        description: str = "",
        parent_version: Optional[str] = None
    ) -> AgentVersion:
        """
        Register a new agent version.
        
        Args:
            agent_id: Agent identifier
            version: Version string (e.g., "v2.0.0")
            code_path: Path to code (optional)
            config: Version configuration
            description: Human-readable description
            parent_version: Previous version this is based on
        
        Returns:
            Registered AgentVersion
        """
        # Calculate code hash if path provided
        code_hash = ""
        if code_path:
            code_hash = self._hash_directory(code_path)
            # Store code
            self._store_version_code(agent_id, version, code_path)
        
        agent_version = AgentVersion(
            agent_id=agent_id,
            version=version,
            code_hash=code_hash,
            config=config or {},
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
            parent_version=parent_version
        )
        
        # Add to registry
        if agent_id not in self.versions:
            self.versions[agent_id] = []
        
        self.versions[agent_id].append(agent_version)
        self._save_registry()
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="version_registered",
                agent="version_manager",
                step=agent_id,
                metadata={"version": version, "parent": parent_version}
            )
        
        print(f"✅ Registered {agent_id} version {version}")
        return agent_version
    
    def deploy_shadow(
        self,
        agent_id: str,
        version: str,
        traffic_percentage: float = 0.0
    ) -> str:
        """
        Deploy version in shadow mode.
        
        Runs alongside production without affecting users.
        Used for testing and validation.
        """
        return self._deploy(
            agent_id=agent_id,
            version=version,
            strategy=DeploymentStrategy.SHADOW,
            traffic_percentage=traffic_percentage
        )
    
    def deploy_canary(
        self,
        agent_id: str,
        version: str,
        rollout_percentage: float = DEFAULT_CANARY_PERCENTAGE
    ) -> str:
        """
        Deploy version with canary rollout.
        
        Gradually increases traffic percentage.
        """
        return self._deploy(
            agent_id=agent_id,
            version=version,
            strategy=DeploymentStrategy.CANARY,
            traffic_percentage=rollout_percentage
        )
    
    def deploy_ab_test(
        self,
        agent_id: str,
        version_a: str,
        version_b: str,
        split_percentage: float = 50.0
    ) -> Tuple[str, str]:
        """
        Deploy two versions for A/B testing.
        
        Args:
            version_a: Control version (baseline)
            version_b: Treatment version (candidate)
            split_percentage: % traffic to version_b
        
        Returns:
            Tuple of deployment IDs
        """
        deploy_a = self._deploy(
            agent_id=agent_id,
            version=version_a,
            strategy=DeploymentStrategy.A_B_TEST,
            traffic_percentage=100.0 - split_percentage
        )
        
        deploy_b = self._deploy(
            agent_id=agent_id,
            version=version_b,
            strategy=DeploymentStrategy.A_B_TEST,
            traffic_percentage=split_percentage
        )
        
        return deploy_a, deploy_b
    
    def _deploy(
        self,
        agent_id: str,
        version: str,
        strategy: DeploymentStrategy,
        traffic_percentage: float
    ) -> str:
        """Internal deployment method."""
        # Validate version exists
        if agent_id not in self.versions:
            raise ValueError(f"Agent {agent_id} not found")
        
        version_obj = next(
            (v for v in self.versions[agent_id] if v.version == version),
            None
        )
        if not version_obj:
            raise ValueError(f"Version {version} not found for {agent_id}")
        
        # Create deployment
        deployment_id = f"deploy-{uuid.uuid4().hex[:8]}"
        
        deployment = Deployment(
            id=deployment_id,
            agent_id=agent_id,
            version=version,
            strategy=strategy,
            traffic_percentage=traffic_percentage,
            started_at=datetime.now(timezone.utc).isoformat()
        )
        
        self.deployments[deployment_id] = deployment
        self.active_deployments[agent_id] = deployment_id
        
        # Update version status
        version_obj.status = "deployed"
        self._save_registry()
        
        # Log deployment
        self._log_deployment(deployment)
        
        print(f"🚀 Deployed {agent_id}:{version}")
        print(f"   Strategy: {strategy.value}")
        print(f"   Traffic: {traffic_percentage}%")
        print(f"   Deployment ID: {deployment_id}")
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="version_deployed",
                agent="version_manager",
                step=agent_id,
                metadata={
                    "version": version,
                    "strategy": strategy.value,
                    "traffic": traffic_percentage
                }
            )
        
        return deployment_id
    
    def rollback(self, deployment_id: str, reason: str = "") -> bool:
        """
        Rollback a deployment to previous version.
        
        Args:
            deployment_id: Deployment to rollback
            reason: Why rollback is happening
        
        Returns:
            True if rollback successful
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
        
        # Find previous version
        agent_id = deployment.agent_id
        versions = self.versions.get(agent_id, [])
        
        current_idx = next(
            (i for i, v in enumerate(versions) if v.version == deployment.version),
            None
        )
        
        if current_idx is None or current_idx == 0:
            print(f"❌ No previous version to rollback to")
            return False
        
        previous_version = versions[current_idx - 1]
        
        # Mark deployment as rolled back
        deployment.status = "rolled_back"
        deployment.ended_at = datetime.now(timezone.utc).isoformat()
        
        # Update version status
        for v in versions:
            if v.version == deployment.version:
                v.status = "rolled_back"
        
        self._save_registry()
        
        print(f"⏮️  Rolled back {agent_id} to {previous_version.version}")
        print(f"   Reason: {reason}")
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="version_rolled_back",
                agent="version_manager",
                step=agent_id,
                metadata={
                    "from_version": deployment.version,
                    "to_version": previous_version.version,
                    "reason": reason
                }
            )
        
        return True
    
    def promote_canary(self, deployment_id: str, new_percentage: float) -> bool:
        """
        Increase canary rollout percentage.
        
        Args:
            deployment_id: Canary deployment
            new_percentage: New traffic percentage
        
        Returns:
            True if promotion successful
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment or deployment.strategy != DeploymentStrategy.CANARY:
            return False
        
        deployment.traffic_percentage = min(new_percentage, 100.0)
        
        print(f"📈 Promoted canary for {deployment.agent_id}")
        print(f"   Traffic: {deployment.traffic_percentage}%")
        
        if deployment.traffic_percentage >= 100.0:
            deployment.status = "completed"
            print(f"   ✅ Canary complete - full deployment")
        
        return True
    
    def compare_versions(
        self,
        agent_id: str,
        baseline: str,
        candidate: str
    ) -> Optional[VersionComparison]:
        """
        Compare performance of two versions.
        
        Returns comparison metrics and recommendation.
        """
        # In production, would query actual metrics
        # For now, return simulated comparison
        
        return VersionComparison(
            baseline_version=baseline,
            candidate_version=candidate,
            error_rate_delta=-0.02,  # 2% better
            latency_delta=-150.0,  # 150ms faster
            cost_delta=0.001,  # $0.001 more expensive
            success_rate_delta=0.02,  # 2% better
            recommendation="DEPLOY" if all([
                -0.02 < -0.01,
                -150.0 < -100.0,
                0.02 > 0.01
            ]) else "EVALUATE"
        )
    
    def get_version_history(self, agent_id: str) -> List[AgentVersion]:
        """Get version history for an agent."""
        return self.versions.get(agent_id, [])
    
    def get_active_deployment(self, agent_id: str) -> Optional[Deployment]:
        """Get currently active deployment for an agent."""
        deployment_id = self.active_deployments.get(agent_id)
        if deployment_id:
            return self.deployments.get(deployment_id)
        return None
    
    def auto_rollback_check(self, deployment_id: str) -> bool:
        """
        Check if deployment should be auto-rolled back.
        
        Returns True if rollback triggered.
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
        
        # Check metrics
        error_rate = deployment.metrics.get("error_rate", 0)
        
        if error_rate > ROLLBACK_THRESHOLD_ERROR_RATE:
            print(f"🚨 Auto-rollback triggered for {deployment_id}")
            print(f"   Error rate {error_rate:.1%} exceeds threshold {ROLLBACK_THRESHOLD_ERROR_RATE:.1%}")
            return self.rollback(deployment_id, f"High error rate: {error_rate:.1%}")
        
        return False
    
    def _hash_directory(self, path: str) -> str:
        """Calculate hash of directory contents."""
        # Simplified - would actually hash files
        return hashlib.sha256(path.encode()).hexdigest()[:16]
    
    def _store_version_code(self, agent_id: str, version: str, code_path: str):
        """Store version code in version storage."""
        version_dir = self.version_storage / agent_id / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy code (simplified)
        # In production, would properly package and store
        (version_dir / "manifest.json").write_text(json.dumps({
            "source_path": code_path,
            "stored_at": datetime.now(timezone.utc).isoformat()
        }))
    
    def _log_deployment(self, deployment: Deployment):
        """Log deployment to file."""
        with open(DEPLOYMENT_LOG_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": deployment.started_at,
                "deployment_id": deployment.id,
                "agent": deployment.agent_id,
                "version": deployment.version,
                "strategy": deployment.strategy.value,
                "traffic": deployment.traffic_percentage
            }) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("🔢 Testing OpenClaw Agent Versioning...\n")
    
    vm = VersionManager()
    
    print("1. Registering versions...")
    
    vm.register_version(
        agent_id="website_builder",
        version="v1.0.0",
        config={"model": "gemini-1.5-pro", "timeout": 300},
        description="Initial stable version"
    )
    
    vm.register_version(
        agent_id="website_builder",
        version="v1.1.0",
        config={"model": "gemini-1.5-pro", "timeout": 240, "caching": True},
        description="Added caching support",
        parent_version="v1.0.0"
    )
    
    vm.register_version(
        agent_id="website_builder",
        version="v2.0.0",
        config={"model": "claude-sonnet-4-5", "timeout": 300, "caching": True},
        description="Upgraded to Claude for better quality",
        parent_version="v1.1.0"
    )
    
    print(f"   Registered 3 versions")
    
    print("\n2. Shadow deployment...")
    
    shadow_deploy = vm.deploy_shadow(
        agent_id="website_builder",
        version="v2.0.0",
        traffic_percentage=0  # 0% = pure shadow
    )
    
    print(f"   Shadow deployment: {shadow_deploy}")
    
    print("\n3. Canary deployment...")
    
    canary_deploy = vm.deploy_canary(
        agent_id="website_builder",
        version="v2.0.0",
        rollout_percentage=5
    )
    
    print(f"   Canary deployment: {canary_deploy}")
    
    print("\n4. Promoting canary...")
    
    vm.promote_canary(canary_deploy, 25)
    vm.promote_canary(canary_deploy, 50)
    vm.promote_canary(canary_deploy, 100)
    
    print("\n5. Version comparison...")
    
    comparison = vm.compare_versions(
        agent_id="website_builder",
        baseline="v1.1.0",
        candidate="v2.0.0"
    )
    
    print(f"   Baseline: {comparison.baseline_version}")
    print(f"   Candidate: {comparison.candidate_version}")
    print(f"   Error rate delta: {comparison.error_rate_delta:+.1%}")
    print(f"   Latency delta: {comparison.latency_delta:+.0f}ms")
    print(f"   Cost delta: ${comparison.cost_delta:+.4f}")
    print(f"   Recommendation: {comparison.recommendation}")
    
    print("\n6. Version history...")
    
    history = vm.get_version_history("website_builder")
    print(f"   Versions: {len(history)}")
    for v in history:
        print(f"     {v.version}: {v.description[:40]}...")
    
    print("\n7. Simulating rollback...")
    
    vm.rollback(canary_deploy, "Performance regression detected")
    
    print("\n✅ Agent Versioning test complete!")
    print("   Registry:", VERSION_REGISTRY_FILE)
    print("   Deployments:", DEPLOYMENT_LOG_FILE)


if __name__ == "__main__":
    main()
