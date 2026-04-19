#!/bin/bash
#
# Model Consistency Checker
# Verifies spawned agents use correct preferred models
# Usage: bash model-consistency-check.sh [session-key]
#

set -e

WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
AGENT_DIR="$WORKSPACE/agent-directory.json"
LOG_FILE="$WORKSPACE/model-mismatch-$(date +%Y-%m-%d).log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Model Consistency Checker${NC}"
echo "========================================"
echo "Time: $TIMESTAMP"
echo ""

# Load agent directory
if [ ! -f "$AGENT_DIR" ]; then
    echo -e "${RED}❌ Error: agent-directory.json not found${NC}"
    exit 1
fi

# Parse session key if provided
if [ -n "$1" ]; then
    SESSION_KEY="$1"
    echo -e "${BLUE}Checking session: $SESSION_KEY${NC}"
    
    # Extract agent name from session key
    # Format: agent:quality:subagent:session-id
    AGENT_NAME=$(echo "$SESSION_KEY" | cut -d: -f2)
    
    # Get session status (simplified - would need actual API call)
    echo -e "${YELLOW}⚠ Note: Full session status check requires OpenClaw API${NC}"
    echo "For now, checking configuration consistency..."
else
    echo -e "${BLUE}Checking all agent configurations...${NC}"
fi

echo ""
echo -e "${BLUE}📋 Agent Preferred Models:${NC}"
echo ""

# Check each agent's configuration
python3 -c "
import json
import sys

with open('$AGENT_DIR', 'r') as f:
    data = json.load(f)

agents = data.get('agents', {})
issues = []

print('Agent Configuration Check:')
print('-' * 50)

for agent_id, agent in agents.items():
    name = agent.get('name', agent_id)
    handle = agent.get('handle', '@' + agent_id)
    preferred = agent.get('preferred_model', 'MISSING')
    configured = agent.get('model', 'MISSING')
    
    # Check for issues
    status = '✅'
    if preferred == 'MISSING':
        status = '❌'
        issues.append(f'{name}: Missing preferred_model field')
    elif configured == 'MISSING':
        status = '❌'
        issues.append(f'{name}: Missing model field')
    elif preferred != configured:
        status = '⚠️'
        issues.append(f'{name}: preferred_model ({preferred}) ≠ model ({configured})')
    
    print(f'{status} {name} ({handle})')
    print(f'   Preferred: {preferred}')
    print(f'   Configured: {configured}')
    print()

if issues:
    print('\\nIssues Found:')
    for issue in issues:
        print(f'  • {issue}')
    
    # Log to file
    with open('$LOG_FILE', 'a') as log:
        log.write(f'$TIMESTAMP\\n')
        for issue in issues:
            log.write(f'  {issue}\\n')
        log.write('\\n')
    
    print(f'\\nLogged to: $LOG_FILE')
    sys.exit(1)
else:
    print('✅ All agents properly configured')
    sys.exit(0)
"

EXIT_CODE=$?

echo ""
echo "========================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Model configuration consistent${NC}"
else
    echo -e "${YELLOW}⚠ Model configuration issues found${NC}"
    echo "Check $LOG_FILE for details"
fi

echo ""
echo -e "${BLUE}📝 Quick Check Commands:${NC}"
echo "1. Check agent config: python3 -c \"import json; data=json.load(open('$AGENT_DIR')); print(json.dumps(data['agents'], indent=2))\""
echo "2. View logs: tail -20 $LOG_FILE"
echo "3. Manual spawn check: sessions_spawn(agentId='quality', model='anthropic/claude-sonnet-4-5', ...)"
echo ""

# Check if we can get actual session status
if command -v openclaw &> /dev/null; then
    echo -e "${BLUE}🔄 Checking OpenClaw status...${NC}"
    openclaw status 2>&1 | grep -E "(Model:|🧠)" | head -2
fi

echo ""
echo -e "${BLUE}🔧 Protocol v2.1 Compliance:${NC}"
echo "• Always specify model=agent.preferred_model in spawn calls"
echo "• Verify with session_status after spawn"
echo "• Header must show actual runtime model"
echo "• Log mismatches to $LOG_FILE"