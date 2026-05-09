#!/bin/bash
#
# OpenClaw Cron Setup Script
# Purpose: Safely add the daily health monitor and GitHub progression cron jobs on macOS.
# This script handles backup, idempotency, and gives clear instructions for the macOS security prompt.
#
set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ OpenClaw Cron Setup Script ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# ── macOS Check ──────────────────────────────────────────────────────────────
if [[ "$(uname -s)" != "Darwin" ]]; then
 echo "❌ This script is designed for macOS only."
 echo " On Linux, use your distro's cron setup method."
 exit 1
fi

echo "🖥️ Detected macOS. Proceeding..."
echo

# ── Paths (customize if your OpenClaw install is elsewhere) ─────────────────
OPENCLAW_BASE="$HOME/.openclaw/workspace"
TOOLS_DIR="$OPENCLAW_BASE/tools"
LOGS_DIR="$OPENCLAW_BASE/logs"

HEALTH_SCRIPT="$TOOLS_DIR/automated-health-monitor.sh"
GITHUB_SCRIPT="$TOOLS_DIR/daily-github-progression.sh"

HEALTH_LOG="$LOGS_DIR/health-monitor.log"
GITHUB_LOG="$LOGS_DIR/github-progression.log"

# ── Verify required scripts exist and are executable ────────────────────────
echo "🔍 Verifying required scripts..."
MISSING=0

if [[ ! -f "$HEALTH_SCRIPT" ]]; then
 echo " ❌ Missing: $HEALTH_SCRIPT"
 MISSING=1
elif [[ ! -x "$HEALTH_SCRIPT" ]]; then
 echo " ⚠️ Not executable: $HEALTH_SCRIPT (fixing...)"
 chmod +x "$HEALTH_SCRIPT"
fi

if [[ ! -f "$GITHUB_SCRIPT" ]]; then
 echo " ❌ Missing: $GITHUB_SCRIPT"
 MISSING=1
elif [[ ! -x "$GITHUB_SCRIPT" ]]; then
 echo " ⚠️ Not executable: $GITHUB_SCRIPT (fixing...)"
 chmod +x "$GITHUB_SCRIPT"
fi

if [[ $MISSING -eq 1 ]]; then
 echo
 echo "❌ One or more required scripts are missing."
 echo " Please ensure both scripts exist in: $TOOLS_DIR"
 exit 1
fi

echo " ✅ Both scripts found and executable."
echo

# ── Create logs directory if it doesn't exist ───────────────────────────────
mkdir -p "$LOGS_DIR"
echo "📁 Logs directory ready: $LOGS_DIR"
echo

# ── Backup existing crontab ─────────────────────────────────────────────────
BACKUP_FILE="/tmp/openclaw_crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
if crontab -l &>/dev/null; then
 crontab -l > "$BACKUP_FILE"
 echo "📦 Existing crontab backed up to: $BACKUP_FILE"
else
 echo "📦 No existing crontab found. Creating fresh one."
 touch "$BACKUP_FILE"
fi
echo

# ── Build new crontab content (idempotent) ──────────────────────────────────
TEMP_FILE="/tmp/openclaw_crontab_new.txt"

{
 # Preserve existing non-OpenClaw entries
 crontab -l 2>/dev/null | grep -vE 'OpenClaw System Health|health-monitor|github-progression' || true

 # Only add OpenClaw section if it doesn't already exist
 if ! crontab -l 2>/dev/null | grep -q "OpenClaw System Health"; then
 cat << EOF

# ─── OpenClaw System Health & GitHub Progression ─────────────────────────────
# Added by setup-openclaw-cron.sh on $(date)
# Health monitoring (runs daily at 22:30)
30 22 * * * $HEALTH_SCRIPT >> $HEALTH_LOG 2>&1
# GitHub progression (runs daily at 23:00)
0 23 * * * $GITHUB_SCRIPT >> $GITHUB_LOG 2>&1
EOF
 else
 echo "# (OpenClaw cron entries already present — skipped duplicate)"
 fi
} > "$TEMP_FILE"

# ── Apply the new crontab ───────────────────────────────────────────────────
echo "🚀 Applying new crontab..."
crontab "$TEMP_FILE"

echo "✅ Crontab updated successfully."
echo

# ── Verify ──────────────────────────────────────────────────────────────────
echo "📋 Current OpenClaw-related cron jobs:"
echo "─────────────────────────────────────"
if crontab -l | grep -E 'health-monitor|github-progression|OpenClaw System Health'; then
 echo "─────────────────────────────────────"
 echo "✅ Verification passed."
else
 echo "⚠️ No OpenClaw entries found after update. Please check manually with: crontab -l"
fi
echo

# ── Final Instructions ──────────────────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ NEXT STEPS ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
echo "║ 1. A macOS security dialog may appear. ║"
echo "║ → Go to System Settings → Privacy & Security ║"
echo "║ → Allow 'Terminal' (or your terminal app) Full Disk Access ║"
echo "║ if prompted. ║"
echo "║ ║"
echo "║ 2. Verify the jobs are scheduled: ║"
echo "║ crontab -l | grep -E 'health|github' ║"
echo "║ ║"
echo "║ 3. Test manually once (optional): ║"
echo "║ $HEALTH_SCRIPT ║"
echo "║ $GITHUB_SCRIPT ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo
echo "🎉 OpenClaw cron setup complete!"
echo " Daily health check: 22:30"
echo " Daily GitHub sync: 23:00"