#!/bin/bash
# =============================================================================
# CodeTrellis Validation Runner — Phase D (WS-8)
# =============================================================================
# Clones public repositories and runs CodeTrellis scans to validate extraction quality.
#
# Usage:
#   ./validation_runner.sh                    # Run all 60 repos
#   ./validation_runner.sh --max 5            # Run first 5 repos only
#   ./validation_runner.sh --category 1       # Run category 1 only (Full-Stack)
#   ./validation_runner.sh --repo nestjs/nest # Run single repo
#   ./validation_runner.sh --resume           # Resume from last completed
#   ./validation_runner.sh --cleanup          # Remove cloned repos after scan
#
# Output:
#   validation-results/<repo_name>.prompt   — CodeTrellis matrix.prompt output
#   validation-results/<repo_name>.json     — CodeTrellis JSON output
#   validation-results/<repo_name>.log      — Scan stderr/timing log
#   validation-results/summary.csv          — Per-repo results summary
#   validation-results/summary.txt          — Human-readable summary
# =============================================================================

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CodeTrellis_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_FILE="$SCRIPT_DIR/repos.txt"
REPOS_DIR="${CodeTrellis_VALIDATION_DIR:-/tmp/codetrellis-validation}"
RESULTS_DIR="$SCRIPT_DIR/validation-results"
TIMEOUT_SECONDS=300
MAX_REPOS=0  # 0 = all
CATEGORY_FILTER=""
SINGLE_REPO=""
RESUME=false
CLEANUP=false

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --max)
            MAX_REPOS="$2"
            shift 2
            ;;
        --category)
            CATEGORY_FILTER="$2"
            shift 2
            ;;
        --repo)
            SINGLE_REPO="$2"
            shift 2
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --repos-dir)
            REPOS_DIR="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT_SECONDS="$2"
            shift 2
            ;;
        --help|-h)
            head -20 "$0" | tail -15
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# --- Setup ---
mkdir -p "$REPOS_DIR" "$RESULTS_DIR"

# Category ranges (line numbers in repos.txt, excluding comments/blanks)
declare -A CATEGORY_NAMES
CATEGORY_NAMES[1]="Full-Stack Applications"
CATEGORY_NAMES[2]="Microservices & Backend"
CATEGORY_NAMES[3]="AI/ML Projects"
CATEGORY_NAMES[4]="DevTools & Infrastructure"
CATEGORY_NAMES[5]="Frontend Frameworks"
CATEGORY_NAMES[6]="Specialized & Edge Cases"

# --- Build repo list ---
get_repos() {
    # Read repos, strip comments and blanks
    local repos=()
    local current_category=0

    while IFS= read -r line; do
        # Skip empty lines
        [[ -z "$line" ]] && continue
        # Track category from comments
        if [[ "$line" == \#* ]]; then
            if [[ "$line" == *"Category"* ]]; then
                current_category=$((current_category + 1))
            fi
            continue
        fi
        # Apply category filter
        if [[ -n "$CATEGORY_FILTER" && "$current_category" != "$CATEGORY_FILTER" ]]; then
            continue
        fi
        repos+=("$line")
    done < "$REPOS_FILE"

    # Single repo mode
    if [[ -n "$SINGLE_REPO" ]]; then
        echo "$SINGLE_REPO"
        return
    fi

    # Max repos limit
    local count=0
    for repo in "${repos[@]}"; do
        echo "$repo"
        count=$((count + 1))
        if [[ "$MAX_REPOS" -gt 0 && "$count" -ge "$MAX_REPOS" ]]; then
            break
        fi
    done
}

# --- Scan a single repository ---
scan_repo() {
    local repo="$1"
    local repo_name
    repo_name=$(echo "$repo" | tr '/' '_')
    local repo_dir="$REPOS_DIR/$repo_name"
    local prompt_file="$RESULTS_DIR/${repo_name}.prompt"
    local json_file="$RESULTS_DIR/${repo_name}.json"
    local log_file="$RESULTS_DIR/${repo_name}.log"

    # Resume mode: skip if already scanned
    if [[ "$RESUME" == true && -f "$prompt_file" && -s "$prompt_file" ]]; then
        echo "  ⏭  Skipping $repo (already scanned)"
        return 0
    fi

    # Clone (shallow, single branch)
    if [[ ! -d "$repo_dir" ]]; then
        echo "  📥 Cloning $repo..."
        if ! git clone --depth 1 --single-branch "https://github.com/$repo.git" "$repo_dir" \
            >> "$log_file" 2>&1; then
            echo "  ❌ Clone failed: $repo"
            echo "CLONE_FAILED" > "$prompt_file"
            return 1
        fi
    else
        echo "  📁 Using cached clone: $repo"
    fi

    # Get repo size info
    local file_count
    file_count=$(find "$repo_dir" -type f | wc -l | tr -d ' ')
    echo "  📊 Files: $file_count"

    # Run CodeTrellis scan — prompt format
    echo "  🔍 Scanning (prompt format)..."
    local start_time
    start_time=$(date +%s)

    # Use timeout (gtimeout on macOS, timeout on Linux)
    local timeout_cmd="timeout"
    if command -v gtimeout &>/dev/null; then
        timeout_cmd="gtimeout"
    elif ! command -v timeout &>/dev/null; then
        # Fallback: no timeout available, use background process
        timeout_cmd=""
    fi

    local exit_code=0
    if [[ -n "$timeout_cmd" ]]; then
        $timeout_cmd "$TIMEOUT_SECONDS" \
            python3 -m codetrellis.cli scan "$repo_dir" --optimal \
            > "$prompt_file" 2>> "$log_file" || exit_code=$?
    else
        # No timeout command available — run with built-in shell timeout
        (
            python3 -m codetrellis.cli scan "$repo_dir" --optimal \
                > "$prompt_file" 2>> "$log_file"
        ) &
        local pid=$!
        local waited=0
        while kill -0 "$pid" 2>/dev/null && [[ $waited -lt $TIMEOUT_SECONDS ]]; do
            sleep 1
            waited=$((waited + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
            exit_code=124  # timeout exit code
        else
            wait "$pid" || exit_code=$?
        fi
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Record timing
    echo "TIMING: ${duration}s (exit=$exit_code)" >> "$log_file"

    # Get output stats
    local line_count=0
    if [[ -f "$prompt_file" && -s "$prompt_file" ]]; then
        line_count=$(wc -l < "$prompt_file" | tr -d ' ')
    fi

    # Check for errors in output
    local has_traceback="false"
    if grep -q "Traceback" "$log_file" 2>/dev/null; then
        has_traceback="true"
    fi

    # Report result
    if [[ $exit_code -eq 124 ]]; then
        echo "  ⏰ TIMEOUT after ${TIMEOUT_SECONDS}s"
    elif [[ $exit_code -ne 0 ]]; then
        echo "  ❌ FAILED (exit=$exit_code, ${duration}s)"
    elif [[ $line_count -lt 10 ]]; then
        echo "  ⚠️  EMPTY output ($line_count lines, ${duration}s)"
    else
        echo "  ✅ OK ($line_count lines, ${duration}s)"
    fi

    # Append to CSV summary
    echo "$repo,$repo_name,$exit_code,$duration,$line_count,$file_count,$has_traceback" \
        >> "$RESULTS_DIR/summary.csv"

    # Cleanup cloned repo if requested
    if [[ "$CLEANUP" == true ]]; then
        rm -rf "$repo_dir"
    fi

    return 0
}

# --- Main ---
echo "================================================================"
echo "  CodeTrellis Public Repository Validation Runner"
echo "  Phase D — WS-8"
echo "================================================================"
echo "  CodeTrellis root:     $CodeTrellis_ROOT"
echo "  Repos dir:     $REPOS_DIR"
echo "  Results dir:   $RESULTS_DIR"
echo "  Timeout:       ${TIMEOUT_SECONDS}s per repo"
echo "  Resume mode:   $RESUME"
echo "  Cleanup mode:  $CLEANUP"
if [[ -n "$CATEGORY_FILTER" ]]; then
    echo "  Category:      $CATEGORY_FILTER (${CATEGORY_NAMES[$CATEGORY_FILTER]:-Unknown})"
fi
if [[ "$MAX_REPOS" -gt 0 ]]; then
    echo "  Max repos:     $MAX_REPOS"
fi
echo "================================================================"
echo ""

# Ensure CodeTrellis is importable
cd "$CodeTrellis_ROOT"
export PYTHONPATH="$CodeTrellis_ROOT:${PYTHONPATH:-}"

# Initialize CSV
if [[ "$RESUME" != true ]]; then
    echo "repo,repo_name,exit_code,duration_s,output_lines,file_count,has_traceback" \
        > "$RESULTS_DIR/summary.csv"
fi

# Collect repos
mapfile -t REPOS < <(get_repos)
TOTAL=${#REPOS[@]}
echo "📋 Repos to scan: $TOTAL"
echo ""

# Scan each repo
PASSED=0
FAILED=0
TIMEOUT_COUNT=0
EMPTY=0

for i in "${!REPOS[@]}"; do
    repo="${REPOS[$i]}"
    idx=$((i + 1))
    echo "[$idx/$TOTAL] $repo"

    if scan_repo "$repo"; then
        repo_name=$(echo "$repo" | tr '/' '_')
        prompt_file="$RESULTS_DIR/${repo_name}.prompt"
        if [[ -f "$prompt_file" ]]; then
            line_count=$(wc -l < "$prompt_file" 2>/dev/null | tr -d ' ')
            content=$(head -1 "$prompt_file" 2>/dev/null || echo "")
            if [[ "$content" == "CLONE_FAILED" ]]; then
                FAILED=$((FAILED + 1))
            elif [[ $line_count -lt 10 ]]; then
                EMPTY=$((EMPTY + 1))
            else
                PASSED=$((PASSED + 1))
            fi
        fi
    else
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# --- Summary ---
echo "================================================================"
echo "  VALIDATION SUMMARY"
echo "================================================================"
echo "  Total repos:   $TOTAL"
echo "  ✅ Passed:     $PASSED"
echo "  ❌ Failed:     $FAILED"
echo "  ⚠️  Empty:      $EMPTY"
echo ""
PASS_RATE=0
if [[ $TOTAL -gt 0 ]]; then
    PASS_RATE=$(( (PASSED * 100) / TOTAL ))
fi
echo "  Pass rate:     ${PASS_RATE}%"
echo "  Target:        >70%"
echo ""
if [[ $PASS_RATE -ge 70 ]]; then
    echo "  🎉 TARGET MET!"
else
    echo "  ⚠️  Below target — run quality_scorer.py for detailed analysis"
fi
echo "================================================================"

# Save human-readable summary
cat <<EOF > "$RESULTS_DIR/summary.txt"
CodeTrellis Validation Summary — Phase D (WS-8)
==========================================
Date: $(date -u +"%Y-%m-%d %H:%M UTC")
CodeTrellis Version: $(python3 -c "from codetrellis.cli import VERSION; print(VERSION)" 2>/dev/null || echo "unknown")
Total repos: $TOTAL
Passed: $PASSED
Failed: $FAILED
Empty: $EMPTY
Pass rate: ${PASS_RATE}%
Target: >70%

Next steps:
  1. Run quality_scorer.py for automated quality scoring
  2. Run analyze_results.py for Gap Analysis Round 2
EOF

echo ""
echo "Results saved to: $RESULTS_DIR/"
echo "Next step: python3 $SCRIPT_DIR/quality_scorer.py"
