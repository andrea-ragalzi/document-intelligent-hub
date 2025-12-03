#!/bin/bash

# Quality Gate Script
# Runs complete quality gate checks and generates HTML report

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="${PROJECT_DIR}/scripts"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
BACKEND_DIR="${PROJECT_DIR}/backend"
REPORT_DIR="${SCRIPTS_DIR}"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
REPORT_FILE="${REPORT_DIR}/report_${TIMESTAMP}.html"
LATEST_REPORT="${REPORT_DIR}/latest.html"

# Thresholds
MAX_COMPLEXITY=15

# Lock file for atomic JSON updates
LOCK_FILE="/tmp/quality_gate_${USER}.lock"

# Results storage
declare -A PHASE_RESULTS
declare -A PHASE_STATUS
declare -A PHASE_DETAILS
OVERALL_STATUS="PASSED"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Quality Gate - Full Analysis       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Start HTTP server for live updates (required for auto-refresh to work)
cd "${SCRIPTS_DIR}"
echo -e "${BLUE}🌐 Starting HTTP server on port 8001...${NC}"
python3 -m http.server 8001 > /dev/null 2>&1 &
HTTP_SERVER_PID=$!

# Save server PID for browser lock verification
echo "$HTTP_SERVER_PID" > /tmp/.quality_gate_server_pid

# Wait a moment for server to start
sleep 1


# Function to update HTML report with current status
update_html_report() {
    local current_status="$1"
    local temp_dir="${2:-${TEMP_RESULTS_DIR}}"

    # ATOMIC LOCK: Acquire exclusive lock before updating JSON
    exec 200>"$LOCK_FILE"
    flock -x 200

    # Generate JSON report using Python script
    python3 "${SCRIPTS_DIR}/generate-report-data.py" \
        "${temp_dir}" \
        "${current_status}" \
        "${SCRIPTS_DIR}/report-data.json"

    # Release lock
    exec 200>&-
}

# Generate initial report
update_html_report "RUNNING"

# Function to open browser (only once per session)
open_browser_once() {
    local url="$1"
    local lock_file="/tmp/.quality_gate_browser_lock"
    local server_pid_file="/tmp/.quality_gate_server_pid"

    # Check if server is still running
    if [ -f "$server_pid_file" ]; then
        local old_pid=$(cat "$server_pid_file")
        if ! kill -0 "$old_pid" 2>/dev/null; then
            # Server is dead, remove stale lock
            rm -f "$lock_file" "$server_pid_file"
        fi
    fi

    if [ -f "$lock_file" ]; then
        echo -e "${BLUE}📊 Browser already open - use existing tab for live updates${NC}"
        echo -e "${BLUE}   Tip: To force reopen, run: rm ${lock_file}${NC}"
        return
    fi

    echo -e "${BLUE}📊 Opening browser...${NC}"

    # Try browsers in order of preference
    for browser_cmd in \
        "firefox-developer-edition --new-tab" \
        "firefox --new-tab" \
        "google-chrome --new-window" \
        "chromium-browser --new-window" \
        "chromium --new-window" \
        "xdg-open" \
        "open"; do

        local browser=$(echo "$browser_cmd" | awk '{print $1}')
        if command -v "$browser" &> /dev/null; then
            $browser_cmd "$url" 2>/dev/null &
            touch "$lock_file"
            echo -e "${BLUE}   ✓ Report opened: ${url}${NC}"
            return
        fi
    done

    echo -e "${YELLOW}   ⚠ No browser found, open manually: ${url}${NC}"
}

# Open report in browser
REPORT_URL="http://localhost:8001/quality-gate-index.html"
open_browser_once "${REPORT_URL}"

echo -e "${BLUE}   (Server running on http://localhost:8001)${NC}"
echo ""

# Temporary directory for parallel execution results
TEMP_RESULTS_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_RESULTS_DIR}" EXIT

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Starting Quality Gate Checks (Parallel Execution)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

#####################################
# FRONTEND CHECKS (in background)
#####################################
(
    echo -e "${BLUE}[FRONTEND] Starting frontend checks...${NC}"

    cd "${FRONTEND_DIR}"

    # Phase 1: Prettier
    PRETTIER_OUTPUT=$(npx prettier --check "**/*.{ts,tsx,js,jsx,json,css}" 2>&1 || true)
    # Count files with formatting issues by counting [warn] lines
    PRETTIER_COUNT=$(echo "$PRETTIER_OUTPUT" | grep -c "^\[warn\]" || true)
    PRETTIER_COUNT=${PRETTIER_COUNT:-0}

    if [ "$PRETTIER_COUNT" -gt 0 ]; then
        echo "FAILED" > "${TEMP_RESULTS_DIR}/prettier_status"
    else
        echo "PASSED" > "${TEMP_RESULTS_DIR}/prettier_status"
    fi
    echo "$PRETTIER_COUNT" > "${TEMP_RESULTS_DIR}/prettier_count"
    echo "$PRETTIER_OUTPUT" > "${TEMP_RESULTS_DIR}/prettier_details"
    echo -e "${GREEN}[FRONTEND] ✓ Prettier check completed${NC}"
    update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"

    # Phase 2: TypeScript
    TS_OUTPUT=$(npx tsc --noEmit 2>&1 || true)
    if [ -z "$TS_OUTPUT" ]; then
        TS_ERROR_COUNT=0
        TS_WARNING_COUNT=0
    else
        TS_ERROR_COUNT=$(echo "$TS_OUTPUT" | grep -c "error TS" || true)
        TS_WARNING_COUNT=$(echo "$TS_OUTPUT" | grep -cE "warning TS|deprecated" || true)
        # Ensure numeric values
        TS_ERROR_COUNT=${TS_ERROR_COUNT:-0}
        TS_WARNING_COUNT=${TS_WARNING_COUNT:-0}
    fi

    if [ "$TS_ERROR_COUNT" -eq 0 ]; then
        echo "PASSED" > "${TEMP_RESULTS_DIR}/typescript_status"
    else
        echo "FAILED" > "${TEMP_RESULTS_DIR}/typescript_status"
    fi
    echo "$TS_ERROR_COUNT" > "${TEMP_RESULTS_DIR}/typescript_errors"
    echo "$TS_WARNING_COUNT" > "${TEMP_RESULTS_DIR}/typescript_warnings"
    echo "$TS_OUTPUT" > "${TEMP_RESULTS_DIR}/typescript_details"
    echo -e "${GREEN}[FRONTEND] ✓ TypeScript check completed${NC}"
    update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"

    # Phase 3 & 4: ESLint & Complexity (Optimized: Single Run with JSON parsing)
    # Run ESLint with JSON output
    npm run lint -- -f json > "${TEMP_RESULTS_DIR}/eslint_output.json" 2>/dev/null || true

    # Parse JSON output with Python script
    python3 "${SCRIPTS_DIR}/parse-eslint-output.py" \
        "${TEMP_RESULTS_DIR}/eslint_output.json" \
        "${TEMP_RESULTS_DIR}"

    echo -e "${GREEN}[FRONTEND] ✓ ESLint check completed${NC}"
    update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"

    echo -e "${GREEN}[FRONTEND] ✓ Complexity check completed${NC}"
    update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"

    echo "DONE" > "${TEMP_RESULTS_DIR}/frontend_done"
) &
FRONTEND_PID=$!

#####################################
# BACKEND CHECKS (in background)
#####################################
(
    echo -e "${BLUE}[BACKEND] Starting backend checks...${NC}"
    cd "${BACKEND_DIR}"

    if [ -d ".venv" ]; then
        source .venv/bin/activate

        # Phase 6: Black
        if command -v black &> /dev/null; then
            BLACK_OUTPUT=$(black --check app/ tests/ 2>&1 || true)
            if echo "$BLACK_OUTPUT" | grep -q "would be reformatted"; then
                BLACK_COUNT=$(echo "$BLACK_OUTPUT" | grep -oE '[0-9]+ files? would be reformatted' | grep -oE '^[0-9]+' || echo "0")
                [ -z "$BLACK_COUNT" ] && BLACK_COUNT="0"
                echo "FAILED" > "${TEMP_RESULTS_DIR}/black_status"
            else
                BLACK_COUNT=0
                echo "PASSED" > "${TEMP_RESULTS_DIR}/black_status"
            fi
            echo "$BLACK_COUNT" > "${TEMP_RESULTS_DIR}/black_count"
            echo "$BLACK_OUTPUT" > "${TEMP_RESULTS_DIR}/black_details"
            echo -e "${GREEN}[BACKEND] ✓ Black check completed${NC}"
            update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"
        else
            echo "SKIPPED" > "${TEMP_RESULTS_DIR}/black_status"
            echo "N/A" > "${TEMP_RESULTS_DIR}/black_count"
        fi

        # Phase 7: MyPy (Swapped with Pylint)
        if [ -x ".venv/bin/mypy" ] || command -v mypy &> /dev/null; then
            if [ -x ".venv/bin/mypy" ]; then
                MYPY_OUTPUT=$(.venv/bin/mypy app/ --config-file=pyproject.toml 2>&1 || true)
            else
                MYPY_OUTPUT=$(mypy app/ --config-file=pyproject.toml 2>&1 || true)
            fi
            MYPY_ERROR_COUNT=$(echo "$MYPY_OUTPUT" | grep -c ": error:" || true)
            MYPY_WARNING_COUNT=$(echo "$MYPY_OUTPUT" | grep -c ": note:" || true)

            # Ensure numeric values (grep -c returns 0 on no match, which is valid)
            MYPY_ERROR_COUNT=${MYPY_ERROR_COUNT:-0}
            MYPY_WARNING_COUNT=${MYPY_WARNING_COUNT:-0}

            if [ "${MYPY_ERROR_COUNT}" -eq 0 ]; then
                echo "PASSED" > "${TEMP_RESULTS_DIR}/mypy_status"
            else
                echo "FAILED" > "${TEMP_RESULTS_DIR}/mypy_status"
            fi
            echo "$MYPY_ERROR_COUNT" > "${TEMP_RESULTS_DIR}/mypy_errors"
            echo "$MYPY_WARNING_COUNT" > "${TEMP_RESULTS_DIR}/mypy_notes"
            echo "$MYPY_OUTPUT" > "${TEMP_RESULTS_DIR}/mypy_details"
            echo -e "${GREEN}[BACKEND] ✓ Mypy check completed${NC}"
            update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"
        else
            echo "SKIPPED" > "${TEMP_RESULTS_DIR}/mypy_status"
            echo "N/A" > "${TEMP_RESULTS_DIR}/mypy_errors"
            echo "N/A" > "${TEMP_RESULTS_DIR}/mypy_notes"
        fi

        # Phase 8: Pylint (Swapped with MyPy)
        if command -v pylint &> /dev/null; then
            # Analyze entire backend (app, scripts, tests) with parallel jobs
            PYLINT_OUTPUT=$(pylint app/ scripts/ tests/ --ignore=chroma_db,__pycache__,htmlcov,.venv,logs --jobs=0 2>&1 || true)
            PYLINT_ERROR_COUNT=$(echo "$PYLINT_OUTPUT" | grep -cE ": [EF][0-9]+:" || true)
            PYLINT_WARNING_COUNT=$(echo "$PYLINT_OUTPUT" | grep -c ": W[0-9]*:" || true)
            PYLINT_CONVENTION_COUNT=$(echo "$PYLINT_OUTPUT" | grep -c ": C[0-9]*:" || true)
            PYLINT_REFACTOR_COUNT=$(echo "$PYLINT_OUTPUT" | grep -c ": R[0-9]*:" || true)
            PYLINT_INFO_COUNT=$(echo "$PYLINT_OUTPUT" | grep -c ": I[0-9]*:" || true)

            # Ensure numeric values with default fallback
            PYLINT_ERROR_COUNT=${PYLINT_ERROR_COUNT:-0}

            if [ "$PYLINT_ERROR_COUNT" -eq 0 ]; then
                echo "PASSED" > "${TEMP_RESULTS_DIR}/pylint_status"
            else
                echo "FAILED" > "${TEMP_RESULTS_DIR}/pylint_status"
            fi
            echo "$PYLINT_ERROR_COUNT" > "${TEMP_RESULTS_DIR}/pylint_errors"
            echo "$PYLINT_WARNING_COUNT" > "${TEMP_RESULTS_DIR}/pylint_warnings"
            echo "$PYLINT_CONVENTION_COUNT" > "${TEMP_RESULTS_DIR}/pylint_conventions"
            echo "$PYLINT_REFACTOR_COUNT" > "${TEMP_RESULTS_DIR}/pylint_refactors"
            echo "$PYLINT_INFO_COUNT" > "${TEMP_RESULTS_DIR}/pylint_info"
            echo "$PYLINT_OUTPUT" > "${TEMP_RESULTS_DIR}/pylint_details"
            echo -e "${GREEN}[BACKEND] ✓ Pylint check completed${NC}"
            update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"
        else
            echo "SKIPPED" > "${TEMP_RESULTS_DIR}/pylint_status"
            echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_errors"
            echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_warnings"
            echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_conventions"
            echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_refactors"
            echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_info"
        fi

        # Phase 9: Lizard
        if command -v lizard &> /dev/null; then
            # Analyze entire backend with thread parallelism
            LIZARD_OUTPUT=$(lizard app/ scripts/ tests/ -C 15 --exclude "*/chroma_db/*" --exclude "*/__pycache__/*" --exclude "*/htmlcov/*" --threads 4 2>&1 || true)
            # Count functions in the warning section (between header and === separator)
            LIZARD_COUNT=$(echo "$LIZARD_OUTPUT" | sed -n '/!!!! Warnings/,/^Total nloc/p' | grep -c '@app/' || true)

            # Ensure numeric value with default fallback
            LIZARD_COUNT=${LIZARD_COUNT:-0}

            if [ "$LIZARD_COUNT" -eq 0 ]; then
                echo "PASSED" > "${TEMP_RESULTS_DIR}/lizard_status"
            else
                echo "FAILED" > "${TEMP_RESULTS_DIR}/lizard_status"
            fi
            echo "$LIZARD_COUNT" > "${TEMP_RESULTS_DIR}/lizard_count"
            echo "$LIZARD_OUTPUT" > "${TEMP_RESULTS_DIR}/lizard_details"
            echo -e "${GREEN}[BACKEND] ✓ Lizard check completed${NC}"
            update_html_report "RUNNING" "${TEMP_RESULTS_DIR}"
        else
            echo "SKIPPED" > "${TEMP_RESULTS_DIR}/lizard_status"
            echo "N/A" > "${TEMP_RESULTS_DIR}/lizard_count"
        fi

        deactivate
    else
        echo "SKIPPED" > "${TEMP_RESULTS_DIR}/black_status"
        echo "SKIPPED" > "${TEMP_RESULTS_DIR}/pylint_status"
        echo "SKIPPED" > "${TEMP_RESULTS_DIR}/mypy_status"
        echo "SKIPPED" > "${TEMP_RESULTS_DIR}/lizard_status"
        echo "N/A" > "${TEMP_RESULTS_DIR}/black_count"
        echo "N/A" > "${TEMP_RESULTS_DIR}/pylint_errors"
        echo "N/A" > "${TEMP_RESULTS_DIR}/mypy_errors"
        echo "N/A" > "${TEMP_RESULTS_DIR}/lizard_count"
    fi

    echo "DONE" > "${TEMP_RESULTS_DIR}/backend_done"
) &
BACKEND_PID=$!

# Wait for both frontend and backend to complete
echo -e "${YELLOW}Waiting for frontend and backend checks to complete...${NC}"
wait $FRONTEND_PID
wait $BACKEND_PID

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}All Checks Complete${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Determine overall status by reading from temp files
for phase in prettier typescript eslint complexity black mypy pylint lizard; do
    status=$(cat "${TEMP_RESULTS_DIR}/${phase}_status" 2>/dev/null || echo "PENDING")
    if [ "$status" = "FAILED" ]; then
        OVERALL_STATUS="FAILED"
        break
    fi
done

# Update final report with overall status
update_html_report "${OVERALL_STATUS}"

echo ""

#####################################
# Generate Summary
#####################################
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Quality Gate Summary           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Determine overall status display
if [ "$OVERALL_STATUS" = "PASSED" ]; then
    STATUS_COLOR="green"
    ICON="✓"
    echo -e "${GREEN}Overall Status: ✓ PASSED${NC}"
else
    STATUS_COLOR="red"
    ICON="✗"
    echo -e "${RED}Overall Status: ✗ FAILED${NC}"
fi

echo ""
echo -e "${MAGENTA}Phase Results:${NC}"
for phase in prettier typescript eslint complexity black mypy pylint lizard; do
    status=$(cat "${TEMP_RESULTS_DIR}/${phase}_status" 2>/dev/null || echo "UNKNOWN")
    if [ "$status" = "PASSED" ]; then
        echo -e "  ${GREEN}✓${NC} ${phase}: ${GREEN}${status}${NC}"
    elif [ "$status" = "FAILED" ]; then
        echo -e "  ${RED}✗${NC} ${phase}: ${RED}${status}${NC}"
    else
        echo -e "  ${YELLOW}⚠${NC} ${phase}: ${YELLOW}${status}${NC}"
    fi
done
echo ""

# Generate HTML Report
cd "${FRONTEND_DIR}"

# Final report already updated above, no need to call again

# Cleanup is done in update_html_report function

# Print final results
echo ""
echo -e "${GREEN}✓ Report generated successfully!${NC}"
echo -e "  File: ${REPORT_FILE}"
echo -e "  Latest: ${LATEST_REPORT}"
echo ""

# Wait a moment for browser to fetch final status (polling every 100ms)
echo -e "${BLUE}⏳ Waiting 2 seconds for browser to fetch final status...${NC}"
sleep 2

# Close HTTP server now that browser has received final update
echo -e "${BLUE}🛑 Closing HTTP server (PID: ${HTTP_SERVER_PID})...${NC}"
kill ${HTTP_SERVER_PID} 2>/dev/null || true
rm -f /tmp/.quality_gate_server_pid /tmp/.quality_gate_browser_lock
echo -e "${GREEN}✓ Server closed${NC}"

# Exit with appropriate code
if [ "$OVERALL_STATUS" = "PASSED" ]; then
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}   🎉 QUALITY GATE PASSED! 🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════${NC}"
    echo -e "${RED}   ✗ QUALITY GATE FAILED${NC}"
    echo -e "${RED}═══════════════════════════════════════${NC}"
    exit 1
fi
