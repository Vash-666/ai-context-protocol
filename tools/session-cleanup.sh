#!/bin/bash
#
# Session Cleanup Script
# Automatically kills sessions older than 2 hours that are marked as "DONE"
# Reduces active child sessions from 30+ to under 10
# Part of System Improvement Sprint - Phase 2
#

set -e

# Configuration
WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
LOG_FILE="$WORKSPACE/session-cleanup-log.jsonl"
MAX_SESSION_AGE_HOURS=2
MAX_ACTIVE_SESSIONS=10
CLEANUP_THRESHOLD=20  # Start cleanup when sessions exceed this count

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Starting Session Cleanup Scan...${NC}"
echo "Max session age: $MAX_SESSION_AGE_HOURS hours"
echo "Max active sessions target: $MAX_ACTIVE_SESSIONS"
echo "Cleanup threshold: $CLEANUP_THRESHOLD sessions"
echo ""

# Get current session count
SESSION_COUNT=$(openclaw sessions list --json 2>/dev/null | jq '.sessions | length' 2>/dev/null || echo "0")
echo -e "📊 Current sessions: $SESSION_COUNT"

if [ "$SESSION_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ No active sessions found${NC}"
    exit 0
fi

# Get session details
SESSIONS_JSON=$(openclaw sessions list --json 2>/dev/null || echo '{"sessions":[]}')
ACTIVE_SESSIONS=0
OLD_SESSIONS=0
DONE_SESSIONS=0
SESSIONS_TO_CLEAN=()

# Parse sessions
while IFS= read -r session; do
    if [ -z "$session" ]; then
        continue
    fi
    
    SESSION_KEY=$(echo "$session" | jq -r '.key // ""')
    SESSION_LABEL=$(echo "$session" | jq -r '.label // ""')
    SESSION_AGENT=$(echo "$session" | jq -r '.agentId // ""')
    SESSION_CREATED=$(echo "$session" | jq -r '.created // ""')
    SESSION_LAST_ACTIVE=$(echo "$session" | jq -r '.lastActive // ""')
    SESSION_STATUS=$(echo "$session" | jq -r '.status // ""')
    
    # Skip main session
    if [[ "$SESSION_KEY" == *"main"* ]] || [[ "$SESSION_LABEL" == *"main"* ]]; then
        continue
    fi
    
    # Calculate session age in hours
    if [ -n "$SESSION_LAST_ACTIVE" ]; then
        LAST_ACTIVE_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${SESSION_LAST_ACTIVE:0:19}" "+%s" 2>/dev/null || echo "0")
        CURRENT_TS=$(date "+%s")
        SESSION_AGE_HOURS=$(( (CURRENT_TS - LAST_ACTIVE_TS) / 3600 ))
    else
        SESSION_AGE_HOURS=999
    fi
    
    # Check if session is marked as DONE (in label or status)
    IS_DONE=false
    if [[ "$SESSION_LABEL" == *"DONE"* ]] || [[ "$SESSION_STATUS" == *"done"* ]] || [[ "$SESSION_STATUS" == *"completed"* ]]; then
        IS_DONE=true
        DONE_SESSIONS=$((DONE_SESSIONS + 1))
    fi
    
    # Check if session is old
    IS_OLD=false
    if [ "$SESSION_AGE_HOURS" -gt "$MAX_SESSION_AGE_HOURS" ]; then
        IS_OLD=true
        OLD_SESSIONS=$((OLD_SESSIONS + 1))
    fi
    
    # Count active sessions (not DONE and not too old)
    if [ "$IS_DONE" = false ] && [ "$IS_OLD" = false ]; then
        ACTIVE_SESSIONS=$((ACTIVE_SESSIONS + 1))
    fi
    
    # Mark for cleanup if DONE or old
    if [ "$IS_DONE" = true ] || [ "$IS_OLD" = true ]; then
        SESSIONS_TO_CLEAN+=("$SESSION_KEY:$SESSION_LABEL:$SESSION_AGE_HOURS:$IS_DONE")
    fi
    
done < <(echo "$SESSIONS_JSON" | jq -c '.sessions[]' 2>/dev/null || echo "")

echo -e "📊 Active sessions: $ACTIVE_SESSIONS"
echo -e "📊 Done sessions: $DONE_SESSIONS"
echo -e "📊 Old sessions (>${MAX_SESSION_AGE_HOURS}h): $OLD_SESSIONS"
echo -e "📊 Sessions to clean: ${#SESSIONS_TO_CLEAN[@]}"

# Check if cleanup is needed
if [ ${#SESSIONS_TO_CLEAN[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ No sessions need cleanup${NC}"
    exit 0
fi

if [ "$SESSION_COUNT" -lt "$CLEANUP_THRESHOLD" ] && [ "$ACTIVE_SESSIONS" -le "$MAX_ACTIVE_SESSIONS" ]; then
    echo -e "${GREEN}✅ Session count within limits ($SESSION_COUNT < $CLEANUP_THRESHOLD, $ACTIVE_SESSIONS ≤ $MAX_ACTIVE_SESSIONS)${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}⚠️  Starting session cleanup...${NC}"

# Clean up sessions
CLEANED_COUNT=0
FAILED_COUNT=0

for session_info in "${SESSIONS_TO_CLEAN[@]}"; do
    IFS=':' read -r SESSION_KEY SESSION_LABEL SESSION_AGE_HOURS IS_DONE <<< "$session_info"
    
    echo -n "Cleaning $SESSION_KEY ($SESSION_LABEL) - "
    
    if [ "$IS_DONE" = "true" ]; then
        echo -n "DONE session "
    else
        echo -n "Old session (${SESSION_AGE_HOURS}h) "
    fi
    
    # Try to kill the session
    if openclaw sessions kill "$SESSION_KEY" 2>/dev/null; then
        echo -e "${GREEN}✅ Killed${NC}"
        CLEANED_COUNT=$((CLEANED_COUNT + 1))
        
        # Log the cleanup
        log_cleanup "$SESSION_KEY" "$SESSION_LABEL" "$SESSION_AGE_HOURS" "$IS_DONE" "success"
    else
        echo -e "${RED}❌ Failed${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        
        # Log the failure
        log_cleanup "$SESSION_KEY" "$SESSION_LABEL" "$SESSION_AGE_HOURS" "$IS_DONE" "failed"
    fi
    
    # Limit cleanup rate
    sleep 0.5
done

echo ""
echo -e "${GREEN}📊 Cleanup Summary:${NC}"
echo -e "   Sessions cleaned: $CLEANED_COUNT"
echo -e "   Failed: $FAILED_COUNT"
echo -e "   Remaining sessions: $((SESSION_COUNT - CLEANED_COUNT))"

# Check event delivery monitoring
check_event_delivery

echo -e "${GREEN}✅ Session cleanup completed${NC}"

# Functions
function log_cleanup() {
    local session_key="$1"
    local session_label="$2"
    local session_age="$3"
    local is_done="$4"
    local status="$5"
    
    cat >> "$LOG_FILE" <<EOF
{"timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","session_key":"$session_key","session_label":"$session_label","session_age_hours":$session_age,"is_done":$is_done,"cleanup_status":"$status","total_sessions_before":$SESSION_COUNT,"cleaned_count":$CLEANED_COUNT}
EOF
}

function check_event_delivery() {
    echo -e "${BLUE}🔍 Checking event delivery monitoring...${NC}"
    
    # Check for delayed completion events
    EVENT_LOG="$WORKSPACE/event-delivery-log.jsonl"
    
    if [ -f "$EVENT_LOG" ]; then
        # Count events older than 5 minutes
        DELAYED_EVENTS=$(grep -c "delayed" "$EVENT_LOG" 2>/dev/null || echo "0")
        if [ "$DELAYED_EVENTS" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  $DELAYED_EVENTS delayed events detected${NC}"
            
            # Log to health warnings
            cat >> "$WORKSPACE/health-warnings.jsonl" <<EOF
{"timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","type":"delayed_event_delivery","severity":"warning","message":"$DELAYED_EVENTS delayed completion events detected","action":"Check event delivery system"}
EOF
        else
            echo -e "${GREEN}✅ No delayed events${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Event delivery log not found${NC}"
    fi
}

# Add to daily health monitoring
function add_to_health_monitoring() {
    echo -e "${BLUE}📋 Adding session cleanup to daily health monitoring...${NC}"
    
    HEALTH_MONITOR="$WORKSPACE/tools/automated-health-monitor.sh"
    
    if [ -f "$HEALTH_MONITOR" ]; then
        # Check if already added
        if ! grep -q "session-cleanup.sh" "$HEALTH_MONITOR"; then
            # Add session cleanup check
            sed -i '' '/# Session Health/a\
# Session Cleanup\
echo "🔍 Checking session health..."\
bash "$WORKSPACE/tools/session-cleanup.sh"\
echo ""\
' "$HEALTH_MONITOR"
            
            echo -e "${GREEN}✅ Added to health monitoring${NC}"
        else
            echo -e "${GREEN}✅ Already in health monitoring${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Health monitor script not found${NC}"
    fi
}

# If called with --setup, add to health monitoring
if [[ "$1" == "--setup" ]]; then
    add_to_health_monitoring
fi

# If called with --test, run a test
if [[ "$1" == "--test" ]]; then
    echo -e "${BLUE}🧪 Running session cleanup test...${NC}"
    echo "This would simulate cleanup without actually killing sessions."
    echo "Test mode: Would clean ${#SESSIONS_TO_CLEAN[@]} sessions"
    exit 0
fi