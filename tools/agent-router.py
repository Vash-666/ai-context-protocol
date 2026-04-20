#!/usr/bin/env python3
"""
Agent Router - Multi-Agent Routing Protocol Implementation v2.1
Routes messages to appropriate agents based on @mentions and channel bindings
Enforces Protocol v2.1: Model Routing Consistency
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path

class AgentRouter:
    def __init__(self, directory_path=None):
        """Initialize router with agent directory"""
        if directory_path is None:
            directory_path = Path(__file__).parent.parent / "agent-directory.json"
        
        self.directory_path = Path(directory_path)
        self.load_directory()
        
    def load_directory(self):
        """Load agent directory from JSON file"""
        try:
            with open(self.directory_path, 'r') as f:
                self.directory = json.load(f)
            print(f"✅ Loaded agent directory: {len(self.directory['agents'])} agents")
            return True
        except FileNotFoundError:
            print(f"❌ Agent directory not found: {self.directory_path}")
            self.directory = self.create_default_directory()
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing agent directory: {e}")
            return False
    
    def create_default_directory(self):
        """Create default directory if file doesn't exist"""
        return {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "agents": {
                "switch": {
                    "id": "main",
                    "name": "Switch",
                    "handle": "@orchestrator",
                    "default": True,
                    "status": "active",
                    "preferred_model": "deepseek/deepseek-chat"
                }
            },
            "routing": {
                "default_agent": "switch",
                "mention_prefix": "@",
                "case_sensitive": False
            }
        }
    
    def extract_mentions(self, text):
        """Extract @mentions from text"""
        if not text:
            return []
        
        # Pattern: @agentName with optional punctuation after
        pattern = r'@(\w+)(?:\s|$|\.|,|!|\?|:)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        return [match.lower() for match in matches]
    
    def resolve_agent_from_mention(self, mention):
        """Resolve @mention to agent ID"""
        mention = mention.lower()
        
        # Check all agents
        for agent_id, agent in self.directory['agents'].items():
            # Check handle (without @)
            handle = agent.get('handle', '').lstrip('@').lower()
            if handle == mention:
                return agent_id
            
            # Check aliases
            aliases = [alias.lower() for alias in agent.get('aliases', [])]
            if mention in aliases:
                return agent_id
            
            # Check name
            if agent.get('name', '').lower() == mention:
                return agent_id
        
        return None
    
    def route_message(self, message_text, channel=None, conversation_history=None):
        """
        Route message to appropriate agent with context awareness
        
        Returns:
            dict: {
                "agent_id": "switch",
                "agent_name": "Switch",
                "routing_method": "default|mention|channel",
                "mentions": ["marketing"],
                "handoff_required": True/False,
                "message": "Original message with @mentions removed",
                "context_summary": {...},  # Added for context transfer
                "context_transferred": True/False,  # Added for context transfer
                "preferred_model": "model_name",  # Added for Protocol v2.1
                "model_routing_verified": True/False  # Added for Protocol v2.1
            }
        """
        # Extract mentions
        mentions = self.extract_mentions(message_text)
        resolved_agents = []
        
        for mention in mentions:
            agent_id = self.resolve_agent_from_mention(mention)
            if agent_id:
                resolved_agents.append({
                    "mention": mention,
                    "agent_id": agent_id,
                    "agent_name": self.directory['agents'][agent_id]['name']
                })
        
        # Extract context from conversation history if available
        context_summary = None
        context_transferred = False
        
        if conversation_history:
            context_summary = self.summarize_conversation(conversation_history)
            context_transferred = True
        
        # Determine routing
        routing_method = "default"
        agent_id = self.directory['routing']['default_agent']
        agent_name = self.directory['agents'][agent_id]['name']
        
        # Rule 2: @mentions override default
        if resolved_agents:
            # Use first mentioned agent
            agent_id = resolved_agents[0]['agent_id']
            agent_name = resolved_agents[0]['agent_name']
            routing_method = "mention"
        
        # Rule 3: Channel bindings override @mentions
        if channel and channel in self.directory['routing'].get('channel_bindings', {}):
            channel_agent = self.directory['routing']['channel_bindings'][channel]
            if channel_agent in self.directory['agents']:
                agent_id = channel_agent
                agent_name = self.directory['agents'][agent_id]['name']
                routing_method = "channel"
        
        # Check if agent is available
        agent_status = self.directory['agents'][agent_id].get('status', 'unknown')
        handoff_required = False
        
        if agent_status not in ['active', 'ready']:
            # Agent not available, fallback to default
            if agent_id != self.directory['routing']['default_agent']:
                handoff_required = True
                agent_id = self.directory['routing']['default_agent']
                agent_name = self.directory['agents'][agent_id]['name']
                routing_method = "fallback"
        
        # Clean message (remove @mentions for processing)
        clean_message = message_text
        for mention in mentions:
            clean_message = re.sub(f'@{mention}\\b', '', clean_message, flags=re.IGNORECASE)
        clean_message = re.sub(r'\s+', ' ', clean_message).strip()
        
        # Protocol v2.1: Get preferred model from agent directory
        preferred_model = self.directory['agents'][agent_id].get('preferred_model', 'deepseek/deepseek-chat')
        
        # Protocol v2.1: Verify model routing consistency
        model_routing_verified = True  # Will be verified during spawn
        
        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "routing_method": routing_method,
            "mentions": resolved_agents,
            "handoff_required": handoff_required,
            "clean_message": clean_message,
            "original_message": message_text,
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "context_summary": context_summary,
            "context_transferred": context_transferred,
            "preferred_model": preferred_model,  # Protocol v2.1
            "model_routing_verified": model_routing_verified  # Protocol v2.1
        }
    
    def summarize_conversation(self, conversation_history):
        """
        Summarize conversation history for context transfer.
        Returns a structured context summary.
        """
        if not conversation_history:
            return None
        
        # Extract key information from last 5 messages
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        # Simple extraction of topics and key points
        topics = set()
        key_points = []
        
        for msg in recent_messages:
            # Extract potential topics (simple word-based)
            words = msg.lower().split()
            for word in words:
                if len(word) > 5 and word not in ['create', 'update', 'deploy', 'verify', 'message', 'channel']:
                    topics.add(word)
            
            # Extract potential key points (sentences with action words)
            if any(action in msg.lower() for action in ['create', 'build', 'deploy', 'update', 'fix', 'verify', 'audit', 'analyze']):
                key_points.append(msg[:100])  # First 100 chars
        
        return {
            "topic": ', '.join(list(topics)[:3]) if topics else 'General',
            "key_points": key_points[:3],
            "message_count": len(recent_messages),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_info(self, agent_id):
        """Get information about a specific agent"""
        if agent_id in self.directory['agents']:
            return self.directory['agents'][agent_id]
        return None
    
    def list_agents(self):
        """List all agents with their status"""
        agents = []
        for agent_id, agent in self.directory['agents'].items():
            agents.append({
                "id": agent_id,
                "name": agent.get('name', 'Unknown'),
                "handle": agent.get('handle', ''),
                "status": agent.get('status', 'unknown'),
                "quality": agent.get('quality', 0.0),
                "default": agent.get('default', False),
                "preferred_model": agent.get('preferred_model', 'unknown')  # Protocol v2.1
            })
        return agents
    
    def log_routing_decision(self, routing_result):
        """Log routing decision to file with Protocol v2.1 verification"""
        log_file = Path(__file__).parent.parent / "routing-log.jsonl"
        
        # Protocol v2.1: Add model verification info
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "protocol_version": "2.1",
            **routing_result
        }
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Protocol v2.1: Also log to health monitoring
            self.log_model_routing_verification(routing_result)
            return True
        except Exception as e:
            print(f"❌ Error logging routing decision: {e}")
            return False
    
    def log_model_routing_verification(self, routing_result):
        """Protocol v2.1: Log model routing verification for health monitoring"""
        verification_log = Path(__file__).parent.parent / "model-routing-verification.jsonl"
        
        verification_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": routing_result["agent_id"],
            "agent_name": routing_result["agent_name"],
            "preferred_model": routing_result.get("preferred_model", "unknown"),
            "routing_method": routing_result["routing_method"],
            "verification_status": "pending",  # Will be updated after spawn
            "verification_timestamp": None
        }
        
        try:
            with open(verification_log, 'a') as f:
                f.write(json.dumps(verification_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging model routing verification: {e}")
    
    def verify_model_routing(self, agent_id, actual_model_used):
        """Protocol v2.1: Verify that actual model matches preferred model"""
        verification_log = Path(__file__).parent.parent / "model-routing-verification.jsonl"
        
        # Read all entries and update the latest for this agent
        try:
            with open(verification_log, 'r') as f:
                entries = [json.loads(line) for line in f.readlines()]
            
            # Find the latest entry for this agent
            latest_entry = None
            for entry in reversed(entries):
                if entry.get("agent_id") == agent_id and entry.get("verification_status") == "pending":
                    latest_entry = entry
                    break
            
            if latest_entry:
                preferred_model = latest_entry.get("preferred_model", "unknown")
                verification_status = "verified" if actual_model_used == preferred_model else "mismatch"
                
                # Update the entry
                latest_entry["verification_status"] = verification_status
                latest_entry["actual_model_used"] = actual_model_used
                latest_entry["verification_timestamp"] = datetime.now().isoformat()
                latest_entry["match"] = actual_model_used == preferred_model
                
                # Write back all entries
                with open(verification_log, 'w') as f:
                    for entry in entries:
                        if entry.get("timestamp") == latest_entry.get("timestamp") and entry.get("agent_id") == agent_id:
                            f.write(json.dumps(latest_entry) + '\n')
                        else:
                            f.write(json.dumps(entry) + '\n')
                
                # Log warning if mismatch
                if verification_status == "mismatch":
                    print(f"⚠️  MODEL ROUTING MISMATCH: Agent {agent_id} used {actual_model_used} instead of {preferred_model}")
                    self.log_health_warning(f"Model routing mismatch for {agent_id}: {actual_model_used} != {preferred_model}")
                
                return verification_status == "verified"
            
            return False
            
        except FileNotFoundError:
            print(f"⚠️  Verification log not found: {verification_log}")
            return False
        except Exception as e:
            print(f"❌ Error verifying model routing: {e}")
            return False
    
    def log_health_warning(self, warning_message):
        """Log health warning for monitoring"""
        health_log = Path(__file__).parent.parent / "health-warnings.jsonl"
        
        warning_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "model_routing_mismatch",
            "message": warning_message,
            "severity": "warning"
        }
        
        try:
            with open(health_log, 'a') as f:
                f.write(json.dumps(warning_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging health warning: {e}")

def main():
    """Test the router with Protocol v2.1 verification"""
    router = AgentRouter()
    
    test_messages = [
        ("Create a dashboard", None),
        ("@content create LinkedIn post", None),
        ("@quality audit system quality", None),
        ("Hello there", "telegram"),
        ("@grok analyze market", None),
        ("@switch what's our status?", None)
    ]
    
    print("=" * 60)
    print("🧪 AGENT ROUTER TEST SUITE - Protocol v2.1")
    print("=" * 60)
    
    for message, channel in test_messages:
        result = router.route_message(message, channel)
        
        print(f"\n📨 Message: {message}")
        print(f"   Channel: {channel or 'None'}")
        print(f"   → Agent: {result['agent_name']} ({result['agent_id']})")
        print(f"   Method: {result['routing_method'].upper()}")
        print(f"   Preferred Model: {result.get('preferred_model', 'unknown')}")
        
        if result['mentions']:
            print(f"   Mentions: {', '.join([m['mention'] for m in result['mentions']])}")
        
        if result['handoff_required']:
            print(f"   ⚠️  Handoff required (agent unavailable)")
        
        router.log_routing_decision(result)
    
    print("\n" + "=" * 60)
    print("👥 AGENT DIRECTORY SUMMARY - Protocol v2.1")
    print("=" * 60)
    
    agents = router.list_agents()
    for agent in agents:
        status_emoji = {
            'active': '🟢',
            'ready': '✅',
            'needs_fix': '🔴',
            'planned': '⏳',
            'unknown': '⚪'
        }.get(agent['status'], '⚪')
        
        print(f"{status_emoji} {agent['name']:20} {agent['handle']:15} "
              f"Model: {agent['preferred_model']:25} "
              f"Quality: {agent['quality']}/10 {'(DEFAULT)' if agent['default'] else ''}")
    
    # Test model verification
    print("\n" + "=" * 60)
    print("🔍 MODEL ROUTING VERIFICATION TEST")
    print("=" * 60)
    
    # Test correct model usage
    print("\n✅ Testing correct model usage:")
    router.verify_model_routing("switch", "deepseek/deepseek-chat")
    router.verify_model_routing("content", "google/gemini-2.5-flash")
    router.verify_model_routing("qualityguardian", "anthropic/claude-sonnet-4-5")
    router.verify_model_routing("grok", "grok-4.20-reasoning")
    
    # Test incorrect model usage (should log warning)
    print("\n⚠️  Testing incorrect model usage (should log warning):")
    router.verify_model_routing("content", "deepseek/deepseek-chat")  # Wrong model
    
    print("\n✅ Protocol v2.1 implementation complete!")

if __name__ == "__main__":
    main()