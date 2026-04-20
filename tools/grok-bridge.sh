#!/bin/bash
#
# Grok Bridge Script v2.1
# Secure wrapper for xAI Grok API with cost tracking and credit management
# Usage: bash grok-bridge.sh "Your question"
#        bash grok-bridge.sh --model grok-4.20-code "Your question"
#

set -e

# Configuration
WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
ENV_FILE="$WORKSPACE/.env"
LOG_FILE="$WORKSPACE/grok-bridge-log.md"
COST_LOG="$WORKSPACE/grok-cost-tracker.jsonl"
HEALTH_LOG="$WORKSPACE/health-warnings.jsonl"
API_URL="https://api.x.ai/v1/chat/completions"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")
START_TIME=$(date +%s.%N)

# Default model
MODEL="grok-4.20-reasoning"
SYSTEM_PROMPT="You are Grok, an AI assistant created by xAI. Provide helpful, accurate, and engaging responses."

# Cost tracking (estimated USD per million tokens)
# Source: x.ai pricing (estimated)
COST_PER_MILLION_INPUT=0.50  # $0.50 per million input tokens
COST_PER_MILLION_OUTPUT=1.50 # $1.50 per million output tokens

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
USER_MESSAGE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --system)
            SYSTEM_PROMPT="$2"
            shift 2
            ;;
        *)
            USER_MESSAGE="$1"
            shift
            ;;
    esac
done

# If no message provided, check if piped
if [ -z "$USER_MESSAGE" ] && ! [ -t 0 ]; then
    USER_MESSAGE=$(cat)
fi

# Validate input
if [ -z "$USER_MESSAGE" ]; then
    echo -e "${RED}❌ Error: No message provided${NC}"
    echo "Usage: bash grok-bridge.sh \"Your question\""
    echo "       bash grok-bridge.sh --model grok-4.20-code \"Your question\""
    echo "       echo \"Your question\" | bash grok-bridge.sh"
    exit 1
fi

# Load API key
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: .env file not found at $ENV_FILE${NC}"
    exit 1
fi

# Source .env safely (avoid exporting)
GROK_API_KEY=$(grep GROK_API_KEY "$ENV_FILE" | cut -d= -f2- | tr -d ' ' | tr -d '"' | tr -d "'")

if [ -z "$GROK_API_KEY" ]; then
    echo -e "${RED}❌ Error: GROK_API_KEY not found in .env${NC}"
    exit 1
fi

# Validate API key format (basic check)
if [[ ! "$GROK_API_KEY" =~ ^xai- ]]; then
    echo -e "${YELLOW}⚠ Warning: API key doesn't start with 'xai-'. Check .env file.${NC}"
fi

echo -e "${BLUE}🤖 Calling Grok API (model: $MODEL)...${NC}"
echo ""

# Prepare API request
JSON_PAYLOAD=$(cat <<EOF
{
  "model": "$MODEL",
  "messages": [
    {
      "role": "system",
      "content": "$SYSTEM_PROMPT"
    },
    {
      "role": "user",
      "content": "$USER_MESSAGE"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 4000,
  "stream": false
}
EOF
)

# Make API call
RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $GROK_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" \
  --max-time 30 \
  --retry 2 \
  --retry-delay 1)

END_TIME=$(date +%s.%N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc | awk '{printf "%.2f", $1}')

# Check for errors
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to connect to xAI API${NC}"
    echo "Check network connectivity and API key validity."
    exit 1
fi

# Check if response contains error
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    ERROR_CODE=$(echo "$RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
    
    echo -e "${RED}❌ API Error: $ERROR_MSG${NC}"
    echo -e "${YELLOW}Code: $ERROR_CODE${NC}"
    
    # Special handling for common errors
    if [[ "$ERROR_CODE" == "Some resource has been exhausted" ]] || [[ "$ERROR_MSG" == *"credit"* ]] || [[ "$ERROR_MSG" == *"exhausted"* ]]; then
        echo ""
        echo "⚠️  ⚠️  ⚠️  CREDIT EXHAUSTION DETECTED ⚠️  ⚠️  ⚠️"
        echo ""
        echo "ℹ️  This means:"
        echo "   1. Account credits exhausted"
        echo "   2. Monthly spending limit reached"
        echo "   3. Rate limit exceeded"
        echo ""
        echo "🔧 **ACTION REQUIRED:**"
        echo "   1. Visit: https://x.ai/account/billing"
        echo "   2. Add credits or raise spending limit"
        echo "   3. Check usage dashboard"
        echo ""
        echo "📊 **Current API Key:** ${GROK_API_KEY:0:10}..."
        echo ""
        
        # Log credit exhaustion warning
        log_credit_exhaustion_warning "$ERROR_MSG" "$ERROR_CODE"
    fi
    
    exit 1
fi

# Extract response content
GROK_RESPONSE=$(echo "$RESPONSE" | grep -o '"content":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')

if [ -z "$GROK_RESPONSE" ]; then
    echo -e "${YELLOW}⚠ Warning: Empty response from Grok API${NC}"
    echo "Raw response:"
    echo "$RESPONSE" | head -100
    exit 1
fi

# Extract token usage (if available)
TOKENS_INPUT=$(echo "$RESPONSE" | grep -o '"prompt_tokens":[0-9]*' | cut -d: -f2)
TOKENS_OUTPUT=$(echo "$RESPONSE" | grep -o '"completion_tokens":[0-9]*' | cut -d: -f2)
TOKENS_TOTAL=$(echo "$RESPONSE" | grep -o '"total_tokens":[0-9]*' | cut -d: -f2)

# Calculate estimated cost
ESTIMATED_COST=0
if [ -n "$TOKENS_INPUT" ] && [ -n "$TOKENS_OUTPUT" ]; then
    COST_INPUT=$(echo "scale=6; $TOKENS_INPUT * $COST_PER_MILLION_INPUT / 1000000" | bc)
    COST_OUTPUT=$(echo "scale=6; $TOKENS_OUTPUT * $COST_PER_MILLION_OUTPUT / 1000000" | bc)
    ESTIMATED_COST=$(echo "scale=6; $COST_INPUT + $COST_OUTPUT" | bc)
fi

# Format output
echo -e "${GREEN}🤖 **Grok Response** ($MODEL)${NC}"
if [ -n "$TOKENS_TOTAL" ]; then
    if [ -n "$ESTIMATED_COST" ] && [ "$ESTIMATED_COST" != "0" ]; then
        echo -e "${BLUE}⏱️ ${RESPONSE_TIME}s | 📊 ${TOKENS_TOTAL} tokens | 💰 \$${ESTIMATED_COST}${NC}"
    else
        echo -e "${BLUE}⏱️ ${RESPONSE_TIME}s | 📊 ${TOKENS_TOTAL} tokens${NC}"
    fi
else
    echo -e "${BLUE}⏱️ ${RESPONSE_TIME}s${NC}"
fi
echo ""

echo "$GROK_RESPONSE"
echo ""
echo "---"
echo "*Model: $MODEL | Time: $TIMESTAMP*"

# Log the call
log_grok_call "$USER_MESSAGE" "$GROK_RESPONSE" "$MODEL" "$TIMESTAMP" "$RESPONSE_TIME" "$TOKENS_INPUT" "$TOKENS_OUTPUT" "$TOKENS_TOTAL" "$ESTIMATED_COST"

echo ""
echo -e "${GREEN}✅ Logged to: $LOG_FILE${NC}"

# Functions
function log_grok_call() {
    local user_message="$1"
    local grok_response="$2"
    local model="$3"
    local timestamp="$4"
    local response_time="$5"
    local tokens_input="$6"
    local tokens_output="$7"
    local tokens_total="$8"
    local estimated_cost="$9"
    
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Log to markdown file
    cat >> "$LOG_FILE" <<EOF
## $timestamp

**Model:** $model  
**Input:** ${#user_message} chars  
**Response:** ${#grok_response} chars  
**Time:** ${response_time}s  
**Tokens:** ${tokens_total:-unknown} (in:${tokens_input:-?}, out:${tokens_output:-?})  
**Cost:** \$${estimated_cost:-unknown}

**Question:**  
$user_message

**Response:**  
$grok_response

---

EOF
    
    # Log to cost tracker (JSONL format)
    if [ -n "$tokens_total" ]; then
        cat >> "$COST_LOG" <<EOF
{"timestamp":"$timestamp","model":"$model","tokens_input":${tokens_input:-0},"tokens_output":${tokens_output:-0},"tokens_total":${tokens_total:-0},"estimated_cost":${estimated_cost:-0},"response_time":${response_time},"message_length":${#user_message}}
EOF
    fi
}

function log_credit_exhaustion_warning() {
    local error_msg="$1"
    local error_code="$2"
    
    cat >> "$HEALTH_LOG" <<EOF
{"timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","type":"grok_credit_exhaustion","severity":"critical","message":"Grok API credit exhausted: $error_msg","code":"$error_code","action_required":"Add credits at https://x.ai/account/billing","api_key_prefix":"${GROK_API_KEY:0:10}"}
EOF
    
    echo -e "${YELLOW}⚠ Credit exhaustion logged to health monitoring${NC}"
}

# Health check function (can be called separately)
function grok_health_check() {
    echo -e "${BLUE}🔍 Running Grok Bridge Health Check...${NC}"
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ .env file missing${NC}"
        return 1
    fi
    
    # Check if API key exists
    if ! grep -q "GROK_API_KEY" "$ENV_FILE"; then
        echo -e "${RED}❌ GROK_API_KEY not found in .env${NC}"
        return 1
    fi
    
    # Check API key format
    GROK_API_KEY=$(grep GROK_API_KEY "$ENV_FILE" | cut -d= -f2- | tr -d ' ' | tr -d '"' | tr -d "'")
    if [[ ! "$GROK_API_KEY" =~ ^xai- ]]; then
        echo -e "${YELLOW}⚠ API key format warning${NC}"
    fi
    
    # Check recent cost logs
    if [ -f "$COST_LOG" ]; then
        RECENT_COST=$(tail -10 "$COST_LOG" | jq -s 'map(.estimated_cost) | add' 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ Recent estimated cost: \$${RECENT_COST:-0}${NC}"
    fi
    
    # Check for recent credit exhaustion warnings
    if [ -f "$HEALTH_LOG" ]; then
        CREDIT_WARNINGS=$(grep -c "grok_credit_exhaustion" "$HEALTH_LOG" 2>/dev/null || echo "0")
        if [ "$CREDIT_WARNINGS" -gt 0 ]; then
            echo -e "${RED}❌ $CREDIT_WARNINGS credit exhaustion warnings detected${NC}"
            echo "   Check: $HEALTH_LOG"
        else
            echo -e "${GREEN}✅ No credit exhaustion warnings${NC}"
        fi
    fi
    
    echo -e "${GREEN}✅ Grok Bridge health check passed${NC}"
    return 0
}

# If script called with --health-check
if [[ "$1" == "--health-check" ]]; then
    grok_health_check
    exit $?
fi