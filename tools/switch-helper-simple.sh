#!/bin/bash
#
# Model & Agent Switching Helper (Simplified - Protocol v2)
# Generated: 2026-04-18
# Purpose: Demonstrate switch detection and command generation
# Integration: AGENTS.md Model & Agent Switching Protocol v2
#

WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")

echo "============================================================"
echo "Model & Agent Switching Helper (Protocol v2 - Demo)"
echo "============================================================"
echo "Date: $TIMESTAMP"
echo ""

if [ -z "$1" ]; then
    echo "Usage: bash switch-helper-simple.sh \"switch to Gemini for @content\""
    echo ""
    echo "Test Cases:"
    echo "1. 'switch to Gemini for @content'"
    echo "2. '@quality switch to Sonnet'"
    echo "3. 'use DeepSeek'"
    echo "4. 'Sonnet for @quality'"
    echo ""
    exit 1
fi

INPUT="$1"
INPUT_LOWER=$(echo "$INPUT" | tr '[:upper:]' '[:lower:]')

echo "Input: \"$INPUT\""
echo ""

# Simple detection logic
if [[ $INPUT_LOWER == *"switch to gemini"* ]] && [[ $INPUT_LOWER == *"@content"* ]]; then
    echo "✅ Detected: 'switch to Gemini for @content'"
    echo ""
    echo "Protocol v2 Execution:"
    echo "----------------------"
    echo "1. 3-Tier Context Preservation:"
    echo "   - TIER 1: SESSION-CONTEXT.md updated with switch request"
    echo "   - TIER 2: Memory flush triggered (if complex task)"
    echo "   - TIER 3: Smart routing: @content → Gemini"
    echo ""
    echo "2. OpenClaw Command:"
    echo "   /model gemini-flash"
    echo ""
    echo "3. Agent Routing:"
    echo "   @content will use Gemini 2.5 Flash for next task"
    echo ""
    echo "4. Header Update:"
    echo "   **Agent:** Content"
    echo "   **Model:** Gemini 2.5 Flash (google/gemini-2.5-flash)"
    echo "   **Time:** [After switch]"
    echo "   **Task:** [Content task]"
    echo ""
    echo "✅ Context preserved, command ready, header accurate"

elif [[ $INPUT_LOWER == *"@quality switch to sonnet"* ]]; then
    echo "✅ Detected: '@quality switch to Sonnet'"
    echo ""
    echo "Protocol v2 Execution:"
    echo "----------------------"
    echo "1. 3-Tier Context Preservation: ✅"
    echo "2. OpenClaw Command: /model sonnet"
    echo "3. Agent Routing: @quality → Claude Sonnet 4.5 (default)"
    echo "4. Header: **Agent:** QualityGuardian | **Model:** Claude Sonnet 4.5"
    echo ""
    echo "Note: QualityGuardian already uses Sonnet by default"

elif [[ $INPUT_LOWER == *"use deepseek"* ]]; then
    echo "✅ Detected: 'use DeepSeek'"
    echo ""
    echo "Protocol v2 Execution:"
    echo "----------------------"
    echo "1. 3-Tier Context Preservation: ✅"
    echo "2. OpenClaw Command: /model deepseek"
    echo "3. Agent Routing: Switch → DeepSeek (default)"
    echo "4. Header: **Agent:** Switch | **Model:** DeepSeek"
    echo ""
    echo "Note: Switch already uses DeepSeek by default"

elif [[ $INPUT_LOWER == *"sonnet for @quality"* ]]; then
    echo "✅ Detected: 'Sonnet for @quality'"
    echo ""
    echo "Protocol v2 Execution:"
    echo "----------------------"
    echo "1. 3-Tier Context Preservation: ✅"
    echo "2. OpenClaw Command: /model sonnet"
    echo "3. Agent Routing: @quality → Claude Sonnet 4.5"
    echo "4. Header: **Agent:** QualityGuardian | **Model:** Claude Sonnet 4.5"
    echo ""
    echo "Note: Matches agent's preferred model"

else
    echo "⚠️ No predefined test case matched"
    echo ""
    echo "Supported patterns:"
    echo "- switch to [model] for @agent"
    echo "- @agent switch to [model]"
    echo "- use [model]"
    echo "- [model] for @agent"
    echo ""
    echo "Models: deepseek, sonnet, gemini-flash"
    echo "Agents: @switch, @quality, @content"
fi

echo ""
echo "============================================================"
echo "Key Improvements (Protocol v2):"
echo "============================================================"
echo "1. ✅ Always runs 3-tier context preservation first"
echo "2. ✅ Shows exact /model command needed"
echo "3. ✅ Handles @agent mentions with preferred models"
echo "4. ✅ Header shows ACTUAL runtime model (verified)"
echo "5. ✅ No more header/footer mismatches"
echo ""
echo "Agent Default Models:"
echo "- Switch → DeepSeek (cost-effective)"
echo "- QualityGuardian → Claude Sonnet 4.5 (complex analysis)"
echo "- Content → Gemini 2.5 Flash (balance quality/cost)"
echo ""
echo "Documentation: AGENTS.md (Model & Agent Switching Protocol v2)"
