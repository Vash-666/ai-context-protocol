#!/bin/bash
#
# Grok Bridge Script
# Secure wrapper for xAI Grok API
# Usage: bash grok-bridge.sh "Your question"
#        bash grok-bridge.sh --model grok-4.20-code "Your question"
#

set -e

# Configuration
WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
ENV_FILE="$WORKSPACE/.env"
LOG_FILE="$WORKSPACE/grok-bridge-log.md"
API_URL="https://api.x.ai/v1/chat/completions"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")
START_TIME=$(date +%s.%N)

# Default model
MODEL="grok-4.20-reasoning"
SYSTEM_PROMPT="You are Grok, an AI assistant created by xAI. Provide helpful, accurate, and engaging responses."

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
    if [[ "$ERROR_CODE" == "Some resource has been exhausted" ]]; then
        echo ""
        echo "ℹ️  This usually means:"
        echo "   1. Account credits exhausted"
        echo "   2. Monthly spending limit reached"
        echo "   3. Rate limit exceeded"
        echo ""
        echo "🔧 Solution: Add credits or raise spending limit at x.ai"
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

# Format output
echo -e "${GREEN}🤖 **Grok Response** ($MODEL)${NC}"
if [ -n "$TOKENS_TOTAL" ]; then
    echo -e "${BLUE}⏱️ ${RESPONSE_TIME}s | 📊 ${TOKENS_TOTAL} tokens (in:${TOKENS_INPUT:-?}, out:${TOKENS_OUTPUT:-?})${NC}"
else
    echo -e "${BLUE}⏱️ ${RESPONSE_TIME}s${NC}"
fi
echo ""

echo "$GROK_RESPONSE"
echo ""
echo "---"
echo "*Model: $MODEL | Time: $TIMESTAMP*"

# Log the call
mkdir -p "$(dirname "$LOG_FILE")"
cat >> "$LOG_FILE" <<EOF
## $TIMESTAMP

**Model:** $MODEL  
**Input:** ${#USER_MESSAGE} chars  
**Response:** ${#GROK_RESPONSE} chars  
**Time:** ${RESPONSE_TIME}s  
**Tokens:** ${TOKENS_TOTAL:-unknown} (in:${TOKENS_INPUT:-?}, out:${TOKENS_OUTPUT:-?})

**Question:**  
$USER_MESSAGE

**Response:**  
$GROK_RESPONSE

---

EOF

echo ""
echo -e "${GREEN}✅ Logged to: $LOG_FILE${NC}"