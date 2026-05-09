#!/usr/bin/env python3
"""
OpenClaw State Kernel (Phase 1 - Production Foundation)
=======================================================
Event-sourced state management with Postgres + Redis.
Durable, recoverable, scalable.

Grok: "Everything else is built on sand until this exists."

Features:
- Event sourcing: All state changes are immutable events
- Postgres: Durable persistence, ACID guarantees
- Redis: Fast caching, pub/sub, session state
- Checkpoints: Recovery points for long workflows
- Agent memory: Persistent across sessions
- Workflow state: Multi-agent coordination

Architecture:
    Agent Action → Event → Postgres ( durability)
                          → Redis ( cache/pubsub)
                          → Checkpoint ( recovery)

Usage:
    from state_kernel import StateKernel
    
    kernel = StateKernel()
    
    # Append event (immutable)
    kernel.append_event(
        workflow_id="wf-123",
        agent="website_builder",
        event_type="task_started",
        data={"task": "build_homepage"}
    )
    
    # Create checkpoint
    checkpoint_id = kernel.create_checkpoint("wf-123")
    
    # Recover from checkpoint
    state = kernel.restore_checkpoint(checkpoint_id)
"""

import json
import hashlib
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from contextlib import contextmanager
import uuid

# Try to import Redis and Postgres libraries
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Import tracer
try:
    from execution_tracer import tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
STATE_DIR = Path.home() / ".openclaw" / "workspace" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Connection settings (can be overridden with env vars)
import os
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://localhost:5432/openclaw")

# Fallback mode (file-based if DBs not available)
USE_FALLBACK = not (REDIS_AVAILABLE and POSTGRES_AVAILABLE)

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Event:
    """Immutable event in the event stream."""
    id: str
    workflow_id: str
    agent: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    sequence: int  # Global sequence number for ordering
    parent_event: Optional[str] = None


@dataclass
class Checkpoint:
    """Recovery checkpoint for workflows."""
    id: str
    workflow_id: str
    sequence: int  # Up to which event
    state_snapshot: Dict[str, Any]
    created_at: str
    agent_states: Dict[str, Any]


@dataclass
class AgentMemory:
    """Persistent agent memory across sessions."""
    agent_id: str
    workflow_id: str
    context: Dict[str, Any]
    updated_at: str
    ttl_seconds: int = 86400  # 24 hour default


# ─────────────────────────────────────────────────────────────────────────────
# State Kernel
# ─────────────────────────────────────────────────────────────────────────────
class StateKernel:
    """
    Event-sourced state management kernel.
    
    Provides:
    - Immutable event log (Postgres)
    - Fast state cache (Redis)
    - Recovery checkpoints
    - Agent memory persistence
    """
    
    def __init__(self, use_fallback: bool = USE_FALLBACK):
        self.use_fallback = use_fallback
        self._sequence = 0
        
        if use_fallback:
            print("⚠️  StateKernel running in FALLBACK mode (file-based)")
            print("   Install redis and psycopg2 for production: pip install redis psycopg2-binary")
            self._init_fallback()
        else:
            self._init_production()
    
    def _init_fallback(self):
        """Initialize file-based fallback storage."""
        self.events_file = STATE_DIR / "events.jsonl"
        self.checkpoints_dir = STATE_DIR / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        self.memory_file = STATE_DIR / "agent_memory.json"
        
        # Load existing sequence number
        if self.events_file.exists():
            with open(self.events_file, "r") as f:
                lines = f.readlines()
                self._sequence = len(lines)
    
    def _init_production(self):
        """Initialize Postgres + Redis connections."""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            print("✅ Redis connected")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.use_fallback = True
            self._init_fallback()
            return
        
        try:
            self.postgres_conn = psycopg2.connect(POSTGRES_URL)
            self._init_postgres_schema()
            print("✅ Postgres connected")
        except Exception as e:
            print(f"❌ Postgres connection failed: {e}")
            self.use_fallback = True
            self._init_fallback()
    
    def _init_postgres_schema(self):
        """Initialize database schema."""
        with self.postgres_conn.cursor() as cur:
            # Events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id UUID PRIMARY KEY,
                    workflow_id VARCHAR(255) NOT NULL,
                    agent VARCHAR(255) NOT NULL,
                    event_type VARCHAR(255) NOT NULL,
                    data JSONB NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    sequence BIGINT NOT NULL,
                    parent_event UUID,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Checkpoints table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id UUID PRIMARY KEY,
                    workflow_id VARCHAR(255) NOT NULL,
                    sequence BIGINT NOT NULL,
                    state_snapshot JSONB NOT NULL,
                    agent_states JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Agent memory table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    agent_id VARCHAR(255) NOT NULL,
                    workflow_id VARCHAR(255) NOT NULL,
                    context JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    ttl_seconds INT DEFAULT 86400,
                    PRIMARY KEY (agent_id, workflow_id)
                );
            """)
            
            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_workflow ON events(workflow_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_sequence ON events(sequence);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow ON checkpoints(workflow_id);")
            
            self.postgres_conn.commit()
    
    def append_event(
        self,
        workflow_id: str,
        agent: str,
        event_type: str,
        data: Dict[str, Any],
        parent_event: Optional[str] = None
    ) -> Event:
        """
        Append immutable event to the event log.
        
        This is the core operation - all state changes go through here.
        """
        self._sequence += 1
        
        event = Event(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            agent=agent,
            event_type=event_type,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            sequence=self._sequence,
            parent_event=parent_event
        )
        
        if self.use_fallback:
            self._append_event_fallback(event)
        else:
            self._append_event_production(event)
        
        # Trace the event
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="state_event",
                agent=agent,
                step=event_type,
                metadata={
                    "workflow_id": workflow_id,
                    "event_id": event.id,
                    "sequence": event.sequence
                }
            )
        
        return event
    
    def _append_event_fallback(self, event: Event):
        """Append event to file-based storage."""
        with open(self.events_file, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
    
    def _append_event_production(self, event: Event):
        """Append event to Postgres + Redis."""
        # Persist to Postgres
        with self.postgres_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (id, workflow_id, agent, event_type, data, timestamp, sequence, parent_event)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event.id, event.workflow_id, event.agent, event.event_type,
                json.dumps(event.data), event.timestamp, event.sequence, event.parent_event
            ))
            self.postgres_conn.commit()
        
        # Cache in Redis
        event_key = f"event:{event.id}"
        self.redis_client.setex(event_key, 3600, json.dumps(asdict(event)))
        
        # Publish to event stream
        self.redis_client.publish("openclaw:events", json.dumps({
            "workflow_id": event.workflow_id,
            "event_type": event.event_type,
            "sequence": event.sequence
        }))
    
    def get_events(
        self,
        workflow_id: str,
        since_sequence: int = 0
    ) -> List[Event]:
        """Get all events for a workflow since a given sequence."""
        if self.use_fallback:
            return self._get_events_fallback(workflow_id, since_sequence)
        else:
            return self._get_events_production(workflow_id, since_sequence)
    
    def _get_events_fallback(self, workflow_id: str, since_sequence: int) -> List[Event]:
        """Get events from file."""
        events = []
        if not self.events_file.exists():
            return events
        
        with open(self.events_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                if data["workflow_id"] == workflow_id and data["sequence"] > since_sequence:
                    events.append(Event(**data))
        
        return sorted(events, key=lambda e: e.sequence)
    
    def _get_events_production(self, workflow_id: str, since_sequence: int) -> List[Event]:
        """Get events from Postgres."""
        with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM events
                WHERE workflow_id = %s AND sequence > %s
                ORDER BY sequence ASC
            """, (workflow_id, since_sequence))
            
            rows = cur.fetchall()
            return [Event(**dict(row)) for row in rows]
    
    def create_checkpoint(
        self,
        workflow_id: str,
        state_snapshot: Optional[Dict] = None
    ) -> str:
        """
        Create recovery checkpoint for a workflow.
        
        Returns checkpoint ID for later restoration.
        """
        checkpoint_id = str(uuid.uuid4())
        
        # Get current agent states
        agent_states = self._get_agent_states(workflow_id)
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            workflow_id=workflow_id,
            sequence=self._sequence,
            state_snapshot=state_snapshot or {},
            created_at=datetime.now(timezone.utc).isoformat(),
            agent_states=agent_states
        )
        
        if self.use_fallback:
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
            with open(checkpoint_file, "w") as f:
                json.dump(asdict(checkpoint), f)
        else:
            with self.postgres_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO checkpoints (id, workflow_id, sequence, state_snapshot, agent_states)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    checkpoint.id, checkpoint.workflow_id, checkpoint.sequence,
                    json.dumps(checkpoint.state_snapshot), json.dumps(checkpoint.agent_states)
                ))
                self.postgres_conn.commit()
        
        if TRACING_AVAILABLE:
            tracer.record_event(
                event_type="checkpoint_created",
                agent="state_kernel",
                step="checkpoint",
                metadata={"workflow_id": workflow_id, "checkpoint_id": checkpoint_id}
            )
        
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Restore workflow state from checkpoint."""
        if self.use_fallback:
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
            if not checkpoint_file.exists():
                return None
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
                return Checkpoint(**data)
        else:
            with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM checkpoints WHERE id = %s", (checkpoint_id,))
                row = cur.fetchone()
                if row:
                    return Checkpoint(**dict(row))
                return None
    
    def save_agent_memory(
        self,
        agent_id: str,
        workflow_id: str,
        context: Dict[str, Any],
        ttl_seconds: int = 86400
    ):
        """Persist agent memory across sessions."""
        memory = AgentMemory(
            agent_id=agent_id,
            workflow_id=workflow_id,
            context=context,
            updated_at=datetime.now(timezone.utc).isoformat(),
            ttl_seconds=ttl_seconds
        )
        
        if self.use_fallback:
            memories = {}
            if self.memory_file.exists():
                with open(self.memory_file, "r") as f:
                    memories = json.load(f)
            
            key = f"{agent_id}:{workflow_id}"
            memories[key] = asdict(memory)
            
            with open(self.memory_file, "w") as f:
                json.dump(memories, f)
        else:
            with self.postgres_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_memory (agent_id, workflow_id, context, updated_at, ttl_seconds)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id, workflow_id)
                    DO UPDATE SET context = EXCLUDED.context, updated_at = EXCLUDED.updated_at
                """, (agent_id, workflow_id, json.dumps(context), memory.updated_at, ttl_seconds))
                self.postgres_conn.commit()
            
            # Cache in Redis with TTL
            memory_key = f"memory:{agent_id}:{workflow_id}"
            self.redis_client.setex(memory_key, ttl_seconds, json.dumps(context))
    
    def get_agent_memory(self, agent_id: str, workflow_id: str) -> Optional[Dict]:
        """Retrieve agent memory."""
        if self.use_fallback:
            if not self.memory_file.exists():
                return None
            with open(self.memory_file, "r") as f:
                memories = json.load(f)
                key = f"{agent_id}:{workflow_id}"
                memory = memories.get(key)
                return memory["context"] if memory else None
        else:
            # Try Redis first
            memory_key = f"memory:{agent_id}:{workflow_id}"
            cached = self.redis_client.get(memory_key)
            if cached:
                return json.loads(cached)
            
            # Fall back to Postgres
            with self.postgres_conn.cursor() as cur:
                cur.execute("""
                    SELECT context FROM agent_memory
                    WHERE agent_id = %s AND workflow_id = %s
                    AND updated_at > NOW() - INTERVAL '1 second' * ttl_seconds
                """, (agent_id, workflow_id))
                row = cur.fetchone()
                return row[0] if row else None
    
    def _get_agent_states(self, workflow_id: str) -> Dict[str, Any]:
        """Get current state of all agents in workflow."""
        # This is a simplified version - full implementation would track agent states
        return {}
    
    def close(self):
        """Clean up connections."""
        if not self.use_fallback:
            if hasattr(self, 'postgres_conn'):
                self.postgres_conn.close()
            if hasattr(self, 'redis_client'):
                self.redis_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Testing OpenClaw State Kernel...\n")
    
    with StateKernel() as kernel:
        workflow_id = f"workflow-{uuid.uuid4().hex[:8]}"
        
        print(f"1. Creating workflow: {workflow_id}")
        
        # Simulate workflow events
        print("\n2. Appending events...")
        
        event1 = kernel.append_event(
            workflow_id=workflow_id,
            agent="switch",
            event_type="workflow_started",
            data={"task": "build_website", "project": "coffee_shop"}
        )
        print(f"   Event 1: {event1.event_type} (seq: {event1.sequence})")
        
        event2 = kernel.append_event(
            workflow_id=workflow_id,
            agent="website_builder",
            event_type="task_started",
            data={"component": "navbar"},
            parent_event=event1.id
        )
        print(f"   Event 2: {event2.event_type} (seq: {event2.sequence})")
        
        event3 = kernel.append_event(
            workflow_id=workflow_id,
            agent="website_builder",
            event_type="task_completed",
            data={"component": "navbar", "files": ["navbar.html"]}
        )
        print(f"   Event 3: {event3.event_type} (seq: {event3.sequence})")
        
        # Create checkpoint
        print("\n3. Creating checkpoint...")
        checkpoint_id = kernel.create_checkpoint(
            workflow_id=workflow_id,
            state_snapshot={"completed_components": ["navbar"]}
        )
        print(f"   Checkpoint: {checkpoint_id[:8]}...")
        
        # Save agent memory
        print("\n4. Saving agent memory...")
        kernel.save_agent_memory(
            agent_id="website_builder",
            workflow_id=workflow_id,
            context={"preferred_theme": "dark", "last_component": "navbar"}
        )
        print("   Memory saved")
        
        # Retrieve events
        print("\n5. Retrieving events...")
        events = kernel.get_events(workflow_id)
        print(f"   Retrieved {len(events)} events")
        for ev in events:
            print(f"     - {ev.agent}: {ev.event_type}")
        
        # Restore checkpoint
        print("\n6. Restoring checkpoint...")
        checkpoint = kernel.restore_checkpoint(checkpoint_id)
        if checkpoint:
            print(f"   Restored to sequence {checkpoint.sequence}")
            print(f"   State: {checkpoint.state_snapshot}")
        
        # Retrieve memory
        print("\n7. Retrieving agent memory...")
        memory = kernel.get_agent_memory("website_builder", workflow_id)
        if memory:
            print(f"   Memory: {memory}")
    
    print("\n✅ State Kernel test complete!")
    print(f"   Mode: {'Fallback (file-based)' if USE_FALLBACK else 'Production (Postgres + Redis)'}")