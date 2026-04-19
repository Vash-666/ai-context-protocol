#!/bin/bash
# Simple test for xAI Grok API

WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
API_KEY=$(grep GROK_API_KEY "$WORKSPACE/.env" | cut -d= -f2)

echo "Testing xAI Grok API..."
echo "API Key (first 20 chars): ${API_KEY:0:20}..."

# Test 1: Check models endpoint
echo ""
echo "Test 1: Checking available models..."
curl -s -X GET "https://api.x.ai/v1/models" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" | head -100

echo ""
echo "Test 2: Simple chat completion..."
curl -s -X POST "https://api.x.ai/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4.20-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "What is 2+2?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }' | head -200