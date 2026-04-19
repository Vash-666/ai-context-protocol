# TOOLS.md - Local Notes

Environment-specific setup and infrastructure details for Vash's OpenClaw instance.

---

## Messaging & Communication

### Telegram
- **Bot:** vash_ai_bot (or similar)
- **User ID:** 7968379010
- **Status:** ✅ Active and paired
- **Token:** Configured in channels

### Signal
- **Number:** +16468835444
- **Status:** ❌ **DECOMMISSIONED** (2026-04-18 - Quality Cut)
- **CLI Path:** `/Users/rohitvashist/.openclaw/tools/signal-cli/0.13.24/signal-cli`
- **Reason:** Unstable connection, high maintenance burden, low value (5.5/10 quality score)
- **Note:** QR code linking never succeeded despite multiple attempts. Replaced by Telegram (primary) + WebChat (backup).

---

## Website & Domains

### vash1st.com
- **Platform:** WordPress.com (hosted)
- **Login:** rohit.vashist@live.com / Vash1st@1988
- **Status:** Active, content updated Feb 2026
- **Content Files:** 
  - `/workspace/wordpress-homepage-content.md`
  - `/workspace/wordpress-about-content.md`
  - `/workspace/wordpress-work-content.md`
  - `/workspace/wordpress-contact-content.md`
  - `/workspace/wordpress-homepage-expanded.md` (detailed version)

---

## Development Environment

### Machine
- **Device:** Mac Mini (dedicated for OpenClaw/AI work)
- **OS:** macOS (Darwin 24.3.0, arm64)
- **Timezone:** Eastern Time (America/New_York)
- **Location:** Lorton, Virginia area

### Tools Installed
- **VS Code:** Installed via Homebrew for markdown editing
- **Signal CLI:** 0.13.24 (decommissioned)
- **OpenClaw:** 2026.2.9
- **Node:** v25.6.0
- **Shell:** zsh
- **Grok Bridge:** ✅ New (2026-04-18) - tools/grok-bridge.sh

### API Keys Configured
- **DeepSeek:** ✅ Configured (env-secrets.sh)
- **Gemini:** ✅ **Newly added** (env-secrets.sh)
- **Grok (xAI):** ✅ **Newly added** (2026-04-18) - .env file
- **Anthropic:** ⏳ Not configured
- **OpenAI:** ⏳ Not configured

### Dashboard Access
- **URL:** http://localhost:18789/
- **Gateway port:** 18789
- **Status:** ✅ Active and responding

### New Agent Skills (2026-04-18)
- **@grok Bridge:** Secure xAI Grok API integration
  - **Script:** tools/grok-bridge.sh
  - **Key storage:** .env file (gitignored)
  - **Default model:** grok-4.20-reasoning
  - **Usage:** @grok "Your question" or bash tools/grok-bridge.sh "Your question"
  - **Security:** API key never committed, permissions 600
  - **Logging:** grok-bridge-log.md (all calls tracked)

---

## Work Context

### GSA/Federal Systems
- **Current Role:** Principal Business Analyst, GSA
- **Primary Systems:** SAM.gov, FPDS
- **Tech Stack:** Amazon Bedrock, OpenSearch, ServiceNow, Jira, FedRAMP-compliant infrastructure

### Web3/Blockchain
- **Focus Areas:** Tokenization, agentic AI, decentralized governance
- **Certification:** Certified Ethereum Expert

---

## Preferences

### Communication Style
- Direct and efficient - skip pleasantries when working
- Provide reasoning with recommendations
- Deep technical detail when exploring, concise summaries for decisions

### Work Style
- Analytical, data-driven decision making
- Iterative collaboration welcomed
- Proactive suggestions that align with goals

---

## Notes

- Token efficiency matters - batch operations when possible
- Avoid over-explaining basics when context is clear
- Focus on practical innovation over hype

---

## Quality Cut Automation (2026-04-18)

### Purpose
Repeatable system refinement process to keep system lean and mean after project bursts.

### Files Created
- **Process:** `quality-cut-process.md` (complete guide)
- **Cron Script:** `quality-cut-cron.sh` (executable automation)
- **Setup Guide:** `quality-cut-cron-setup.md` (scheduling instructions)
- **@quality Optimization:** `agents/quality/AGENTS.md` (chunking strategy)

### Quick Commands
```bash
# Test dry run:
./quality-cut-cron.sh --dry-run

# Run manually:
./quality-cut-cron.sh

# Schedule monthly (last Saturday 9 AM):
crontab -e
# Add: 0 9 * * 6 [ $(date +\%d) -gt 24 ] && /Users/rohitvashist/.openclaw/workspace/quality-cut-cron.sh
```

### @quality Chunking Strategy (Critical)
**Always chunk complex evaluations:**
- ✅ 5-minute timeout max per chunk
- ✅ Single responsibility per task
- ✅ Pre-compute heavy operations
- ✅ Provide data instead of asking to compute
- ❌ Never combine vector retriever + Quality Equation

**Proven:** Ultra-simplified task = 3-second success (vs. 3+ hour failure)

### Status
- ✅ Process documented
- ✅ Cron script executable
- ✅ @quality optimized for stress jobs
- ⏳ Pending: Schedule in crontab
- ⏳ Pending: Complete Quality Cut Milestone 2-4
