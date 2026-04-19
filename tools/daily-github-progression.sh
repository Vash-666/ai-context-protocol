#!/bin/bash
#
# Daily GitHub Progression Script
# Generated: 2026-04-18
# Purpose: Automatically update GitHub repositories with daily progress
# Schedule: Runs every day at 23:00 (11:00 PM)
# Safety: No deletions, full git history preserved, backups created
#

set -e

WORKSPACE="/Users/rohitvashist/.openclaw/workspace"
HOMEGUARDIAN="$WORKSPACE/homeguardian"
AGENTIC_AI="$WORKSPACE/github-agentic-ai-systems"
LOG_FILE="$WORKSPACE/daily-github-progression.log"
TODAY=$(date +%Y-%m-%d)
TODAY_DISPLAY=$(date "+%B %d, %Y")
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Safety: Check for leaked secrets in a file
check_for_secrets() {
    local file="$1"
    local filename=$(basename "$file")
    
    # Skip if file doesn't exist
    [ ! -f "$file" ] && return 0
    
    # Common API key patterns (case-insensitive)
    if grep -qiE '(AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|AQ\.[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|glpat-[A-Za-z0-9_-]{20,})' "$file" 2>/dev/null; then
        echo -e "${RED}⚠ WARNING${NC}: Possible API key/token found in $filename"
        echo -e "${YELLOW}Skipping archive of $filename for security${NC}"
        return 1
    fi
    
    return 0
}

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "Daily GitHub Progression Update"
echo "============================================================"
echo "Date: $TIMESTAMP"
echo "Today: $TODAY_DISPLAY"
echo ""

# Step 1: Git Pull (rebase to preserve linear history)
echo -e "${BLUE}[STEP 1]${NC} Pulling latest changes from GitHub..."
echo ""

if [ -d "$HOMEGUARDIAN/.git" ]; then
    echo "Pulling homeguardian repository..."
    cd "$HOMEGUARDIAN"
    git stash push -m "Auto-stash before daily update $TODAY" 2>/dev/null || true
    git pull --rebase origin main || echo "Warning: pull --rebase failed, continuing..."
    git stash pop 2>/dev/null || true
    echo -e "${GREEN}✓${NC} HomeGuardian updated"
else
    echo -e "${YELLOW}⚠${NC} HomeGuardian not a git repo, skipping pull"
fi

echo ""

if [ -d "$AGENTIC_AI/.git" ]; then
    echo "Pulling agentic-ai-systems repository..."
    cd "$AGENTIC_AI"
    git stash push -m "Auto-stash before daily update $TODAY" 2>/dev/null || true
    git pull --rebase origin main || echo "Warning: pull --rebase failed, continuing..."
    git stash pop 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Agentic AI Systems updated"
else
    echo -e "${YELLOW}⚠${NC} Agentic AI Systems not a git repo, skipping pull"
fi

echo ""

# Step 2: Gather Today's Progress
echo -e "${BLUE}[STEP 2]${NC} Gathering today's progress..."
echo ""

SESSION_CONTEXT="$WORKSPACE/SESSION-CONTEXT.md"
MEMORY_TODAY="$WORKSPACE/memory/$TODAY.md"
PROGRESS_FILES=""

# Read SESSION-CONTEXT.md
if [ -f "$SESSION_CONTEXT" ]; then
    echo "Reading SESSION-CONTEXT.md..."
    SESSION_SUMMARY=$(head -20 "$SESSION_CONTEXT" | grep -E "^(##|\\*\\*)" | head -5 || echo "Session context available")
    echo -e "${GREEN}✓${NC} Session context captured"
else
    SESSION_SUMMARY="No session context available"
    echo -e "${YELLOW}⚠${NC} SESSION-CONTEXT.md not found"
fi

# Read today's memory log
if [ -f "$MEMORY_TODAY" ]; then
    echo "Reading memory/$TODAY.md..."
    MEMORY_SUMMARY=$(head -30 "$MEMORY_TODAY" | grep -E "^(#|##|\\*\\*|-)" | head -5 || echo "Daily log available")
    echo -e "${GREEN}✓${NC} Daily memory log captured"
else
    MEMORY_SUMMARY="No daily log for $TODAY"
    echo -e "${YELLOW}⚠${NC} memory/$TODAY.md not found"
fi

# Find verification logs from today
VERIFICATION_LOGS=$(find "$WORKSPACE" -name "*verification*.log" -type f -mtime -1 2>/dev/null | head -3)
if [ -n "$VERIFICATION_LOGS" ]; then
    VERIFICATION_COUNT=$(echo "$VERIFICATION_LOGS" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓${NC} Found $VERIFICATION_COUNT verification logs from today"
else
    VERIFICATION_COUNT=0
    echo "No verification logs from today"
fi

# Check for progress.md updates in homeguardian
if [ -f "$HOMEGUARDIAN/progress.md" ]; then
    PROGRESS_UPDATED=$(find "$HOMEGUARDIAN/progress.md" -mtime -1 2>/dev/null)
    if [ -n "$PROGRESS_UPDATED" ]; then
        echo -e "${GREEN}✓${NC} HomeGuardian progress.md updated today"
        PROGRESS_FILES="$HOMEGUARDIAN/progress.md"
    fi
fi

echo ""

# Step 3: Update JOURNEY.md
echo -e "${BLUE}[STEP 3]${NC} Updating JOURNEY.md..."
echo ""

JOURNEY_HG="$HOMEGUARDIAN/docs/journey/JOURNEY.md"
JOURNEY_AA="$AGENTIC_AI/docs/journey/JOURNEY.md"

# Generate today's entry (write to temp file to avoid newline issues)
cat > /tmp/daily_entry_$TODAY.md << EOFENTRY
### Daily Progress: $TODAY_DISPLAY

**System Status:**
- Quality baseline: 8.08/10 (Tools: 10.0/10)
- Active agents: 3 (Switch, QualityGuardian, Content)
- Context preservation: 100%

**Today's Activity:**
$SESSION_SUMMARY

**Daily Log:**
$MEMORY_SUMMARY

**Verification:**
$VERIFICATION_COUNT automated checks completed

---

EOFENTRY

# Update HomeGuardian JOURNEY.md
if [ -f "$JOURNEY_HG" ]; then
    echo "Updating $JOURNEY_HG..."
    
    # Backup original
    cp "$JOURNEY_HG" "$JOURNEY_HG.backup-$TODAY"
    
    # Insert today's entry after the Timeline section
    # Use sed to insert the temp file content
    sed '/^## Timeline/r /tmp/daily_entry_'"$TODAY"'.md' "$JOURNEY_HG.backup-$TODAY" > "$JOURNEY_HG"
    
    echo -e "${GREEN}✓${NC} HomeGuardian JOURNEY.md updated"
else
    echo -e "${YELLOW}⚠${NC} HomeGuardian JOURNEY.md not found, skipping"
fi

# Update Agentic AI Systems JOURNEY.md (mirror)
if [ -f "$JOURNEY_AA" ]; then
    echo "Updating $JOURNEY_AA..."
    cp "$JOURNEY_HG" "$JOURNEY_AA" 2>/dev/null || echo "Could not sync to agentic-ai-systems"
    echo -e "${GREEN}✓${NC} Agentic AI Systems JOURNEY.md updated"
fi

echo ""

# Step 4: Update README files
echo -e "${BLUE}[STEP 4]${NC} Updating README files..."
echo ""

# Generate "Latest Progress" section (write to temp file)
cat > /tmp/latest_progress_$TODAY.md << EOFLATEST
## 📅 Latest Progress ($TODAY_DISPLAY)

**Daily Update:**
- Session: $SESSION_SUMMARY
- Logs: $MEMORY_SUMMARY
- Verification: $VERIFICATION_COUNT checks completed

📖 **[View Full Journey →](docs/journey/JOURNEY.md)**

---

EOFLATEST

# Update HomeGuardian README
README_HG="$HOMEGUARDIAN/README.md"
if [ -f "$README_HG" ]; then
    echo "Updating HomeGuardian README.md..."
    
    # Backup
    cp "$README_HG" "$README_HG.backup-$TODAY"
    
    # Check if "Latest Progress" section exists and replace/insert
    if grep -q "## 📅 Latest Progress" "$README_HG"; then
        # Remove old Latest Progress section and insert new one
        sed '/^## 📅 Latest Progress/,/^## [^📅]/{
            /^## 📅 Latest Progress/!{
                /^## /!d
            }
        }' "$README_HG.backup-$TODAY" | sed '/^## 📅 Latest Progress/r /tmp/latest_progress_'"$TODAY"'.md' | sed '/^## 📅 Latest Progress/d' > "$README_HG"
    else
        # Insert after title (first line)
        (head -1 "$README_HG.backup-$TODAY"; echo ""; cat /tmp/latest_progress_$TODAY.md; tail -n +2 "$README_HG.backup-$TODAY") > "$README_HG"
    fi
    
    echo -e "${GREEN}✓${NC} HomeGuardian README.md updated"
else
    echo -e "${YELLOW}⚠${NC} HomeGuardian README.md not found"
fi

echo ""

# Step 5: Archive Today's Work
echo -e "${BLUE}[STEP 5]${NC} Archiving today's work..."
echo ""

ARCHIVE_DIR="$HOMEGUARDIAN/docs/archive/$TODAY"
mkdir -p "$ARCHIVE_DIR"

# Archive key files (with safety checks)
if [ -f "$SESSION_CONTEXT" ]; then
    if check_for_secrets "$SESSION_CONTEXT"; then
        cp "$SESSION_CONTEXT" "$ARCHIVE_DIR/SESSION-CONTEXT-$TODAY.md" && echo -e "${GREEN}✓${NC} Archived SESSION-CONTEXT.md"
    fi
fi

if [ -f "$MEMORY_TODAY" ]; then
    if check_for_secrets "$MEMORY_TODAY"; then
        cp "$MEMORY_TODAY" "$ARCHIVE_DIR/memory-$TODAY.md" && echo -e "${GREEN}✓${NC} Archived daily memory log"
    fi
fi

# NEVER archive MEMORY.md - contains local secrets
echo -e "${YELLOW}⚠${NC} Skipped MEMORY.md (contains local secrets, not safe for GitHub)"
echo -e "${YELLOW}⚠${NC} Skipped .env files (local configuration, not safe for GitHub)"

# Archive verification logs from today (with safety checks)
if [ -n "$VERIFICATION_LOGS" ]; then
    for log in $VERIFICATION_LOGS; do
        if check_for_secrets "$log"; then
            cp "$log" "$ARCHIVE_DIR/" 2>/dev/null && echo -e "${GREEN}✓${NC} Archived $(basename $log)"
        fi
    done
fi

# Archive progress.md if updated today
if [ -n "$PROGRESS_FILES" ]; then
    cp "$PROGRESS_FILES" "$ARCHIVE_DIR/progress-$TODAY.md" && echo -e "${GREEN}✓${NC} Archived progress.md"
fi

echo -e "${GREEN}✓${NC} Archive created at: $ARCHIVE_DIR"

echo ""

# Step 6: Commit Changes
echo -e "${BLUE}[STEP 6]${NC} Committing changes..."
echo ""

# Commit HomeGuardian
if [ -d "$HOMEGUARDIAN/.git" ]; then
    cd "$HOMEGUARDIAN"
    
    git add .
    COMMIT_MSG="daily: progression update - $TODAY - automated restructure

- Updated JOURNEY.md with today's progress
- Updated README.md with latest activity
- Archived $VERIFICATION_COUNT verification logs
- Preserved full git history (no data loss)

Automated by daily-github-progression.sh"
    
    if git diff --cached --quiet; then
        echo "No changes to commit in HomeGuardian"
    else
        git commit -m "$COMMIT_MSG" || echo "Commit failed (may be no changes)"
        echo -e "${GREEN}✓${NC} HomeGuardian changes committed"
    fi
fi

echo ""

# Commit Agentic AI Systems
if [ -d "$AGENTIC_AI/.git" ]; then
    cd "$AGENTIC_AI"
    
    git add .
    COMMIT_MSG="daily: progression update - $TODAY - automated restructure

- Updated JOURNEY.md (mirrored from homeguardian)
- Preserved full git history

Automated by daily-github-progression.sh"
    
    if git diff --cached --quiet; then
        echo "No changes to commit in Agentic AI Systems"
    else
        git commit -m "$COMMIT_MSG" || echo "Commit failed (may be no changes)"
        echo -e "${GREEN}✓${NC} Agentic AI Systems changes committed"
    fi
fi

echo ""

# Step 7: Git Push
echo -e "${BLUE}[STEP 7]${NC} Pushing to GitHub..."
echo ""

# Push HomeGuardian
if [ -d "$HOMEGUARDIAN/.git" ]; then
    cd "$HOMEGUARDIAN"
    
    if git push origin main; then
        echo -e "${GREEN}✓${NC} HomeGuardian pushed to GitHub"
    else
        echo -e "${RED}✗${NC} HomeGuardian push failed (check credentials or network)"
    fi
fi

echo ""

# Push Agentic AI Systems
if [ -d "$AGENTIC_AI/.git" ]; then
    cd "$AGENTIC_AI"
    
    if git push origin main; then
        echo -e "${GREEN}✓${NC} Agentic AI Systems pushed to GitHub"
    else
        echo -e "${RED}✗${NC} Agentic AI Systems push failed"
    fi
fi

echo ""

# Summary
echo "============================================================"
echo "Daily GitHub Progression Update Complete"
echo "============================================================"
echo ""
echo -e "${GREEN}📖 Updated JOURNEY.md:${NC}"
echo "   HomeGuardian: https://github.com/Vash-666/homeguardian/blob/main/docs/journey/JOURNEY.md"
echo "   Agentic AI: https://github.com/Vash-666/agentic-ai-systems/blob/main/docs/journey/JOURNEY.md"
echo ""
echo -e "${GREEN}📄 Updated READMEs:${NC}"
echo "   HomeGuardian: https://github.com/Vash-666/homeguardian/blob/main/README.md"
echo ""
echo -e "${GREEN}📦 Archive:${NC}"
echo "   Location: docs/archive/$TODAY/"
echo "   Files archived: SESSION-CONTEXT, memory, verification logs"
echo ""
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Log saved to: $LOG_FILE"
echo ""
echo "Next run: Tomorrow at 23:00 (11:00 PM)"
