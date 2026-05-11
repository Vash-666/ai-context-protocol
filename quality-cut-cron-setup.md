# Quality Cut Cron Job Setup

**Purpose:** Automate periodic system refinement to keep system lean and mean  
**Created:** 2026-04-18  
**Status:** Ready for scheduling

---

## 📋 **Files Created**

1. **Process Documentation:** `quality-cut-process.md`
   - Complete step-by-step Quality Cut process
   - Milestones 0-4 with detailed tasks
   - @quality chunking strategy (critical optimization)
   - Expected outcomes and success criteria

2. **Executable Script:** `quality-cut-cron.sh`
   - Automated execution of Milestone 0 (Validation)
   - Health check creation
   - Logging and notification
   - Dry-run mode for testing

3. **@quality Agent Configuration:** `agents/quality/AGENTS.md`
   - Chunking protocol for stress jobs
   - Template tasks for common evaluations
   - Performance optimization strategies
   - Known issues and workarounds

4. **Setup Guide:** `quality-cut-cron-setup.md` (this file)
   - How to schedule cron job
   - Testing instructions
   - Troubleshooting

---

## 🚀 **Quick Start**

### **Test the Script (Dry Run):**
```bash
cd /Users/rohitvashist/.openclaw/workspace
./quality-cut-cron.sh --dry-run
```

This will show what would happen without making changes.

### **Run Manually:**
```bash
cd /Users/rohitvashist/.openclaw/workspace
./quality-cut-cron.sh
```

This executes Milestone 0 (Validation) and creates health check file.

### **Schedule as Cron Job:**

**Option 1: Monthly (Last Saturday, 9 AM)**
```bash
# Add to crontab:
crontab -e

# Add this line:
0 9 * * 6 [ $(date +\%d) -gt 24 ] && /Users/rohitvashist/.openclaw/workspace/quality-cut-cron.sh
```

**Option 2: Quarterly (End of Quarter, 9 AM)**
```bash
# Add to crontab:
crontab -e

# Add this line (March 31, June 30, September 30, December 31):
0 9 31 3,6,9,12 * /Users/rohitvashist/.openclaw/workspace/quality-cut-cron.sh
```

**Option 3: Custom Schedule**
```bash
# Every other Saturday at 9 AM:
0 9 * * 6 [ $(expr $(date +\%W) \% 2) -eq 0 ] && /Users/rohitvashist/.openclaw/workspace/quality-cut-cron.sh

# First Saturday of every month at 9 AM:
0 9 1-7 * 6 /Users/rohitvashist/.openclaw/workspace/quality-cut-cron.sh
```

---

## 📊 **What the Cron Job Does**

### **Automated (Milestone 0 Only):**
1. ✅ Check if OpenClaw is running
2. ✅ Create health check file
3. ✅ Send notification (start)
4. ⏸️ **Pause for human review**
5. ✅ Create log file

### **Manual (Milestones 1-4):**
After Milestone 0 completes and you review the health check:

1. Open OpenClaw chat: `openclaw chat` or web dashboard
2. Ask: `@switch Continue Quality Cut Milestone 1`
3. Follow process in `quality-cut-process.md`
4. Milestones 1-4 execute with human-in-the-loop oversight

**Why not fully automated?**
- Complex decisions require human judgment
- @quality chunking needs monitoring (first few runs)
- Decommissioning items should be reviewed
- Safety: Prevent accidental system breakage

**Future Enhancement:**
Once @quality chunking proves reliable over 3-5 runs, consider full automation.

---

## 🧪 **Testing Instructions**

### **Test 1: Dry Run**
```bash
./quality-cut-cron.sh --dry-run
```

**Expected output:**
- ✅ OpenClaw running check
- ✅ Process document found
- 🧪 Dry run mode message
- ✅ Would execute steps listed
- ✅ Notification logged

### **Test 2: Notify Only**
```bash
./quality-cut-cron.sh --notify-only
```

**Expected output:**
- ✅ Notification sent
- ✅ Exit immediately

### **Test 3: Full Execution (Milestone 0)**
```bash
./quality-cut-cron.sh
```

**Expected output:**
- ✅ Health check file created
- ✅ Log file created in `quality-cut-logs/`
- ⏸️ Pauses for human review
- ✅ Notification sent

### **Test 4: @quality Chunking**

Open OpenClaw chat and test @quality with chunked task:

```
@quality: Score these 4 items (1-10):

1. Quality Equation Tool - Project 7 implementation
2. HomeGuardian - Project 8 monitoring system
3. Vector Context Retriever - Semantic search
4. Agent Router - Message routing system

Criteria:
- Quality: Implementation quality
- Value: Strategic importance
- Maintenance: Effort to maintain

Output: Item name, score, brief reason
Timeout: 5 minutes
```

**Expected:**
- ✅ Completes in 30 seconds to 2 minutes
- ✅ Returns all 4 scores
- ✅ Provides brief reasoning

---

## 🔧 **Configuration Options**

### **Change Schedule Frequency:**

Edit cron schedule based on your needs:

```bash
# Weekly (every Saturday 9 AM):
0 9 * * 6 /path/to/quality-cut-cron.sh

# Bi-weekly (every other Saturday):
0 9 * * 6 [ $(expr $(date +\%W) \% 2) -eq 0 ] && /path/to/quality-cut-cron.sh

# Monthly (last Saturday):
0 9 * * 6 [ $(date +\%d) -gt 24 ] && /path/to/quality-cut-cron.sh

# Quarterly (specific dates):
0 9 31 3,6,9,12 * /path/to/quality-cut-cron.sh
```

### **Change Notification Method:**

Edit `quality-cut-cron.sh` function `send_notification()`:

```bash
send_notification() {
  local message="$1"
  
  # Option 1: Log to file (current)
  echo "$message" >> "$WORKSPACE_DIR/quality-cut-notifications.log"
  
  # Option 2: Send via OpenClaw message tool (when available)
  # openclaw message send --channel telegram --to [user_id] --message "$message"
  
  # Option 3: Send email (requires mail configured)
  # echo "$message" | mail -s "Quality Cut Notification" your@email.com
  
  # Option 4: Desktop notification (macOS)
  # osascript -e "display notification \"$message\" with title \"Quality Cut\""
}
```

### **Change Log Retention:**

Edit script to add log cleanup:

```bash
# Add after log file creation:
# Keep only last 10 Quality Cut logs
log_count=$(ls -1 "$WORKSPACE_DIR/quality-cut-logs/" | wc -l)
if [ "$log_count" -gt 10 ]; then
  ls -1t "$WORKSPACE_DIR/quality-cut-logs/" | tail -n +11 | xargs -I {} rm "$WORKSPACE_DIR/quality-cut-logs/{}"
  log "Cleaned up old log files (kept most recent 10)"
fi
```

---

## 📝 **Log Files**

### **Location:**
```
/Users/rohitvashist/.openclaw/workspace/quality-cut-logs/
```

### **Naming:**
```
quality-cut-YYYY-MM-DD-HHMMSS.log
```

### **Example:**
```
quality-cut-2026-04-18-185600.log
```

### **Contents:**
- Timestamp of run
- System checks (OpenClaw running, process doc found)
- Milestone 0 execution steps
- Health check file location
- Next steps instructions
- Notification status

### **Review Logs:**
```bash
# Latest log:
tail -f /Users/rohitvashist/.openclaw/workspace/quality-cut-logs/quality-cut-*.log | head -100

# All logs:
ls -lht /Users/rohitvashist/.openclaw/workspace/quality-cut-logs/

# Specific log:
cat /Users/rohitvashist/.openclaw/workspace/quality-cut-logs/quality-cut-2026-04-18-185600.log
```

---

## 🚨 **Troubleshooting**

### **Problem: "OpenClaw is not running"**

**Solution:**
```bash
# Start OpenClaw:
openclaw gateway start

# Check status:
openclaw status

# Retry cron job:
./quality-cut-cron.sh
```

### **Problem: "Process document not found"**

**Solution:**
```bash
# Verify file exists:
ls -l /Users/rohitvashist/.openclaw/workspace/quality-cut-process.md

# If missing, document was moved/deleted
# Re-create it or update PROCESS_DOC variable in script
```

### **Problem: Cron job doesn't run**

**Solution:**
```bash
# Check crontab:
crontab -l

# Verify cron syntax:
# Minute Hour Day Month Weekday Command
# 0-59  0-23  1-31 1-12  0-6     /path/to/script

# Check cron logs (macOS):
log show --predicate 'process == "cron"' --last 1h

# Test manually first:
./quality-cut-cron.sh --dry-run
```

### **Problem: @quality still times out**

**Solution:**
1. **Verify chunking:** Check task is using chunk templates from `agents/quality/AGENTS.md`
2. **Reduce chunk size:** If 5 items timeout, try 3 items per chunk
3. **Check timeout setting:** Ensure 5-minute timeout (300 seconds)
4. **Monitor performance:** Track completion time for each chunk
5. **Escalate to technical fix:** Vector retriever optimization (CRITICAL priority)

### **Problem: Notifications not sending**

**Solution:**
```bash
# Check notification log:
tail /Users/rohitvashist/.openclaw/workspace/quality-cut-notifications.log

# Verify OpenClaw message tool configured:
openclaw config get | grep -A10 "message"

# Test notification manually:
echo "Test notification" >> /Users/rohitvashist/.openclaw/workspace/quality-cut-notifications.log
```

---

## 📊 **Performance Expectations**

### **Milestone 0 (Automated):**
- **Duration:** 5-10 seconds
- **Output:** Health check file + log + notification
- **Success rate:** Should be 100% (simple checks only)

### **Milestones 1-4 (Manual with @quality chunking):**
- **Duration:** 2-4 hours total
  - Milestone 1: 1-2 hours (inventory + chunked audits)
  - Milestone 2: 30 minutes (planning)
  - Milestone 3: 1-2 hours (execution)
  - Milestone 4: 30 minutes (validation)
- **@quality chunks:** 5-20 chunks (5 minutes max each)
- **Success rate:** High (each chunk simple and proven)

### **Comparison to Previous Attempt (2026-04-18):**
- **Without chunking:** 4.5 hours lost to @quality failures
- **With chunking:** Expected 2-4 hours productive work
- **Improvement:** 50-75% time savings + higher success rate

---

## 🎯 **Next Steps**

### **Immediate (Tonight - 2026-04-18):**
1. ✅ **Test dry run:** `./quality-cut-cron.sh --dry-run`
2. ✅ **Test full execution:** `./quality-cut-cron.sh`
3. ✅ **Review health check:** Check generated file
4. ✅ **Test @quality chunk:** Use template from agents/quality/AGENTS.md

### **Short-term (Next Week):**
1. **Schedule cron job:** Add to crontab (monthly or quarterly)
2. **Complete Quality Cut Milestone 2-4:** Finish current refinement
3. **Fix vector retriever:** CRITICAL priority (root cause of failures)
4. **Document results:** Update MEMORY.md with outcomes

### **Long-term (Next Quarter):**
1. **Run 2-3 Quality Cut cycles:** Build confidence in process
2. **Refine chunking strategy:** Optimize chunk sizes based on performance
3. **Consider full automation:** If @quality proves reliable
4. **Integrate with project workflow:** Automatic trigger after major projects

---

## 📚 **Related Documentation**

- **Process Guide:** `quality-cut-process.md` (complete step-by-step)
- **@quality Optimization:** `agents/quality/AGENTS.md` (chunking strategy)
- **Current Progress:** `refinement-progress.md` (Quality Cut decisions)
- **Decision Table:** `quality-cut-decision-table.md` (keep/improve/decommission)
- **Technical Defect:** `defects/@quality-technical-issues-2026-04-18.md`

---

## 🎯 **Success Metrics**

Track these after each Quality Cut cycle:

1. **Quality Score:**
   - Before: X.XX/10
   - After: Y.YY/10
   - Target: +0.5 to +1.5 improvement

2. **System Complexity:**
   - Before: N agents, M features
   - After: N-X agents, M-Y features
   - Target: 15-25% reduction

3. **Technical Debt:**
   - Before: N high-priority issues
   - After: N-X issues resolved
   - Target: 2-5 issues resolved per cycle

4. **Time Investment:**
   - Automated (Milestone 0): 5-10 seconds
   - Manual (Milestones 1-4): 2-4 hours
   - Target: <4 hours total

5. **Success Rate:**
   - @quality chunks: X/Y successful
   - Target: >90% success rate

---

_Last updated: 2026-04-18 - Initial cron job setup complete_
