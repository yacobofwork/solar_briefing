#!/bin/bash

#############################################################
#  Solar Briefing - Daily Runner (With Console Output)
#  Purpose: Execute main.py reliably and print basic logs
#############################################################

CRON_LINE=$(crontab -l 2>/dev/null | grep -E "[[:space:]]run_daily\.sh" | head -n 1)

if [ -n "$CRON_LINE" ]; then
    CRON_SCHEDULE=$(echo "$CRON_LINE" | awk '{print $1, $2, $3, $4, $5}')
    echo "[INFO] Cron schedule detected: $CRON_SCHEDULE"
else
    echo "[INFO] No cron schedule found for run_daily.sh"
fi


SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/run_daily.sh"
TARGET_LINK="/usr/local/bin/run_daily.sh"

# Case 1: symlink exists and is correct → no sudo needed
if [ -L "$TARGET_LINK" ] && [ "$(readlink "$TARGET_LINK")" = "$SCRIPT_PATH" ]; then
    echo "[INFO] Symlink already registered:"
    echo "       $TARGET_LINK -> $SCRIPT_PATH"
    REGISTERED=true

# Case 2: symlink exists but wrong → needs sudo once
elif [ -L "$TARGET_LINK" ]; then
    echo "[WARN] Symlink exists but points to a different file."
    echo "[INFO] Fixing symlink (sudo required once)..."
    sudo rm -f "$TARGET_LINK"
    sudo ln -s "$SCRIPT_PATH" "$TARGET_LINK"
    chmod +x "$SCRIPT_PATH"
    echo "[INFO] Symlink corrected:"
    echo "       $TARGET_LINK -> $SCRIPT_PATH"
    REGISTERED=true

# Case 3: symlink missing → needs sudo once
else
    echo "[INFO] Symlink not found. Creating new one (sudo required once)..."
    sudo ln -s "$SCRIPT_PATH" "$TARGET_LINK"
    chmod +x "$SCRIPT_PATH"
    echo "[INFO] Symlink created:"
    echo "       $TARGET_LINK -> $SCRIPT_PATH"
    REGISTERED=true
fi



# Determine the directory where this script is located (project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Switch to the project root directory
cd "$SCRIPT_DIR" || {
    echo "[ERROR] Failed to change directory to project root: $SCRIPT_DIR"
    exit 1
}

# Log file path
LOG_FILE="src/logs/run_daily.log"

# Timestamp
START_TIME="$(date '+%Y-%m-%d %H:%M:%S')"

# Print to terminal
echo "[INFO] Starting run_daily.sh at $START_TIME"
echo "[INFO] Script PID: $$"

# Print to log file
{
    echo "--------------------------------------------------"
    echo "[INFO] Run started at: $START_TIME"
    echo "[INFO] Script PID: $$"
} >> "$LOG_FILE"

# Ensure Python can locate the src package
export PYTHONPATH="$SCRIPT_DIR"

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment..."
    source .venv/bin/activate
else
    echo "[ERROR] Virtual environment not found at .venv/"
    echo "[ERROR] Virtual environment not found at .venv/" >> "$LOG_FILE"
    exit 1
fi

# Execute main.py using module mode
echo "[INFO] Running main.py..."
.venv/bin/python3.11 -m src.system.main >> "$LOG_FILE" 2>&1
STATUS=$?

# Print result to terminal
if [ $STATUS -eq 0 ]; then
    echo "[INFO] Execution completed successfully."
else
    echo "[ERROR] Execution failed with exit code $STATUS."
fi

# Print result to log file
END_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
{
    if [ $STATUS -eq 0 ]; then
        echo "[INFO] Run completed successfully."
    else
        echo "[ERROR] Run failed with exit code $STATUS."
    fi
    echo "[INFO] Run ended at: $END_TIME"
    echo ""
} >> "$LOG_FILE"
