# Grok Bridge Agent Skill (@grok)

**Status:** ✅ Production Ready (2026-04-18)  
**Purpose:** Secure bridge to xAI Grok API for reasoning, analysis, and creative tasks  
**Security:** API key stored in `.env`, never committed to git  
**Integration:** Works with existing 3-agent system (Switch, QualityGuardian, Content)

---

## Quick Start

### From Any Agent:
```bash
# Direct call
@grok "What is the current date and time in EDT?"

# With model override
@grok --model grok-4.20-reasoning "Analyze this complex problem"

# From within agent scripts
bash /workspace/tools/grok-bridge.sh "Your question here"
```

### From Command Line:
```bash
cd /Users/rohitvashist/.openclaw/workspace
bash tools/grok-bridge.sh "Your question"
```

---

## Configuration

### API Key Storage:
- **File:** `/workspace/.env`
- **Format:** `GROK_API_KEY=your-key-here`
- **Security:** File permissions: 600 (owner read/write only)
- **Git:** Added to `.gitignore` (never committed)

### Default Model:
- **Primary:** `grok-4.20-reasoning`
- **Override:** Use `--model model-name` parameter
- **Available Models:**
  - `grok-4.20-reasoning` (default, best for complex analysis)
  - `grok-4.20` (standard)
  - `grok-4.20-vision` (with image support)
  - `grok-4.20-code` (coding tasks)

---

## Usage Examples

### 1. Simple Query:
```bash
@grok "What is 2+2?"
```

**Output:**
```
🤖 **Grok Response** (grok-4.20-reasoning)
⏱️ 0.8s | 📊 42 tokens

The answer is 4.

---

*Model: grok-4.20-reasoning | Time: 2026-04-18 22:10 EDT*
```

### 2. Complex Analysis:
```bash
@grok --model grok-4.20-reasoning "Analyze the ethical implications of AI agents making financial decisions without human oversight."
```

### 3. Code Review:
```bash
@grok --model grok-4.20-code "Review this Python function for security vulnerabilities: [code]"
```

### 4. Creative Writing:
```bash
@grok "Write a short story about an AI that discovers it's running on a Mac Mini in Virginia"
```

---

## Integration with 3-Agent System

### Switch (@orchestrator):
```bash
# Route complex reasoning to Grok
if [ "$TASK_COMPLEXITY" -gt 7 ]; then
    @grok --model grok-4.20-reasoning "$TASK"
fi
```

### QualityGuardian (@quality):
```bash
# Use Grok for deep quality analysis
@grok --model grok-4.20-reasoning "Audit this code for quality issues: $CODE"
```

### Content:
```bash
# Creative content generation
@grok "Generate engaging technical content about: $TOPIC"
```

---

## Bridge Script (`tools/grok-bridge.sh`)

### Features:
- ✅ Secure API key loading from `.env`
- ✅ Model override support (`--model`)
- ✅ Clean markdown output with metadata
- ✅ Automatic logging to `grok-bridge-log.md`
- ✅ Error handling and retry logic
- ✅ Token usage reporting (when available)

### Parameters:
```bash
# Basic usage
bash grok-bridge.sh "Your question"

# With model override
bash grok-bridge.sh --model grok-4.20-code "Your question"

# With system prompt
bash grok-bridge.sh --system "You are a helpful assistant" "Your question"
```

### Output Format:
```
🤖 **Grok Response** (model-name)
⏱️ response_time | 📊 tokens_used

[Response content]

---

*Model: model-name | Time: YYYY-MM-DD HH:MM timezone*
```

---

## Security & Best Practices

### 🔒 Security Rules:
1. **Never commit `.env`** - Already in `.gitignore`
2. **File permissions:** `.env` should be 600 (owner only)
3. **Key rotation:** Rotate API keys quarterly
4. **Usage limits:** Monitor token usage via logs
5. **Audit logs:** All calls logged to `grok-bridge-log.md`

### 📊 Logging:
- **File:** `/workspace/grok-bridge-log.md`
- **Format:** Timestamp, model, input length, response length
- **Retention:** Keep 30 days, archive older logs
- **Monitoring:** Check for unusual patterns

### 💰 Cost Management:
- **Model costs:** grok-4.20-reasoning ≈ $0.01/1K tokens
- **Budget:** Set monthly limits in `.env` (optional)
- **Monitoring:** Review logs weekly for cost trends

---

## Error Handling

### Common Errors:
```bash
# API key missing
❌ Error: GROK_API_KEY not found in .env

# Network issue
❌ Error: Failed to connect to xAI API (check network)

# Rate limit
❌ Error: Rate limit exceeded (429)

# Invalid model
❌ Error: Model 'invalid-model' not available
```

### Recovery:
1. Check `.env` file exists and has correct permissions
2. Verify network connectivity
3. Check xAI API status page
4. Review logs for detailed error messages

---

## Performance

### Expected Response Times:
- **Simple queries:** 0.5-1.5 seconds
- **Complex reasoning:** 2-5 seconds
- **Code generation:** 1-3 seconds

### Token Limits:
- **Input:** ~8,000 tokens (varies by model)
- **Output:** ~4,000 tokens (varies by model)
- **Total:** ~12,000 tokens per call

---

## Integration Examples

### In Agent Scripts:
```bash
#!/bin/bash
# Example: QualityGuardian using Grok for deep audit

QUESTION="Analyze this architecture for scalability issues: $ARCHITECTURE"
RESPONSE=$(bash /workspace/tools/grok-bridge.sh --model grok-4.20-reasoning "$QUESTION")

echo "## Grok Analysis Result"
echo "$RESPONSE"
```

### In OpenClaw Sessions:
```markdown
**Agent:** Switch  
**Task:** Complex reasoning via @grok

@grok --model grok-4.20-reasoning "Analyze this multi-agent coordination problem..."
```

### In Content Generation:
```bash
# Generate technical blog post
TOPIC="Model switching protocols in AI systems"
CONTENT=$(bash /workspace/tools/grok-bridge.sh "Write a technical blog post about: $TOPIC")
echo "$CONTENT" > blog-post.md
```

---

## Maintenance

### Weekly:
- Review `grok-bridge-log.md` for usage patterns
- Check `.env` file permissions
- Verify API key is active

### Monthly:
- Rotate API key (optional, for security)
- Archive old logs
- Review cost vs. value

### Quarterly:
- Update skill documentation
- Check for new xAI models
- Review integration with other agents

---

## Troubleshooting

### Issue: No response
```bash
# Check .env
ls -la .env
cat .env | head -1

# Test connectivity
curl -s https://api.x.ai/v1/models \
  -H "Authorization: Bearer $(grep GROK_API_KEY .env | cut -d= -f2)" \
  -H "Content-Type: application/json"
```

### Issue: Slow responses
- Check network latency
- Try different model (grok-4.20 may be faster than reasoning)
- Reduce input token count

### Issue: Permission errors
```bash
chmod 600 .env
chmod +x tools/grok-bridge.sh
```

---

## Support

### Documentation:
- This file: `/workspace/skills/grok-bridge/SKILL.md`
- Bridge script: `/workspace/tools/grok-bridge.sh`
- Usage logs: `/workspace/grok-bridge-log.md`

### Updates:
- Check for skill updates via clawhub
- Monitor xAI API changelog
- Update skill when new models released

---

## License & Attribution

**Skill:** Grok Bridge Agent (@grok)  
**Author:** Switch (Chief Orchestrator)  
**Created:** 2026-04-18  
**Version:** 1.0  
**Dependencies:** curl, jq (optional), xAI Grok API access

**Security Note:** This skill handles API keys securely. Never share `.env` files or commit them to version control.

---

**Ready to use:** `@grok "Your question here"`