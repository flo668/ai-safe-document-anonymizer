#!/bin/bash
#
# Error Rate Monitoring Script
#
# Monitors error rates from systemd journal for flask-anonimiseren service.
# Alerts when error rate exceeds 5% threshold.
#
# Usage:
#   ./monitor_errors.sh              # Monitor last hour
#   ./monitor_errors.sh --since "2h" # Monitor last 2 hours
#   ./monitor_errors.sh --live       # Continuous monitoring

set -euo pipefail

# Configuration
SERVICE_NAME="flask-anonimiseren"
ERROR_THRESHOLD=0.05  # 5%
TIME_WINDOW="${1:---since "1 hour ago"}"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "==================================================="
echo "Error Rate Monitor - Flask Anonimiseren Tool"
echo "==================================================="
echo ""

# Live monitoring mode
if [[ "${1:-}" == "--live" ]]; then
    echo "📊 Live error monitoring (Ctrl+C to stop)..."
    echo ""
    journalctl -u ${SERVICE_NAME} -f --output=cat | grep --line-buffered '"metric_type"' | while read -r line; do
        # Parse JSON and extract relevant fields
        if echo "$line" | grep -q '"success":false'; then
            file_type=$(echo "$line" | grep -oP '"file_type":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            error=$(echo "$line" | grep -oP '"error":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            echo -e "${RED}❌ ERROR${NC} [$file_type] $error"
        fi

        # Check for alerts
        if echo "$line" | grep -q '"metric_type":"alert"'; then
            alert_msg=$(echo "$line" | grep -oP '"alert_message":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            alert_val=$(echo "$line" | grep -oP '"alert_value":[0-9.]+' | cut -d':' -f2 || echo "0")
            echo -e "${RED}🚨 ALERT${NC} $alert_msg (${alert_val})"
        fi
    done
    exit 0
fi

# Query logs
echo "📖 Querying logs ${TIME_WINDOW}..."
echo ""

# Get processing metrics
LOGS=$(journalctl -u ${SERVICE_NAME} ${TIME_WINDOW} --output=cat 2>/dev/null | grep -E '"metric_type":"processing"' || true)

if [[ -z "$LOGS" ]]; then
    echo -e "${YELLOW}⚠️  No processing metrics found in time window${NC}"
    echo "   The service may not be running or no files were processed."
    exit 0
fi

# Analyze per file type
echo "File Type Error Rates:"
echo "----------------------"

for file_type in xlsx docx pdf txt csv; do
    # Count total and failures for this file type
    total=$(echo "$LOGS" | grep -c "\"file_type\":\"$file_type\"" || echo "0")

    if [[ "$total" -eq "0" ]]; then
        continue
    fi

    failures=$(echo "$LOGS" | grep "\"file_type\":\"$file_type\"" | grep -c '"success":false' || echo "0")

    # Calculate error rate
    error_rate=$(awk "BEGIN {printf \"%.3f\", $failures / $total}")

    # Format output with color
    if (( $(awk "BEGIN {print ($error_rate > $ERROR_THRESHOLD)}") )); then
        status="${RED}🚨 ALERT${NC}"
    elif (( $(awk "BEGIN {print ($error_rate > 0)}") )); then
        status="${YELLOW}⚠️  WARN${NC}"
    else
        status="${GREEN}✓  OK${NC}"
    fi

    error_pct=$(awk "BEGIN {printf \"%.1f\", $error_rate * 100}")

    printf "  %-6s: %3d total, %3d failures (${error_pct}%%) %b\n" \
        "$file_type" "$total" "$failures" "$status"
done

echo ""

# Check for recent alerts
ALERTS=$(journalctl -u ${SERVICE_NAME} ${TIME_WINDOW} --output=cat 2>/dev/null | grep -E '"metric_type":"alert"' || true)

if [[ -n "$ALERTS" ]]; then
    echo -e "${RED}🚨 Recent Alerts:${NC}"
    echo "----------------"
    echo "$ALERTS" | while read -r line; do
        alert_msg=$(echo "$line" | grep -oP '"alert_message":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        alert_val=$(echo "$line" | grep -oP '"alert_value":[0-9.]+' | cut -d':' -f2 || echo "0")
        timestamp=$(echo "$line" | grep -oP '"timestamp":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo "  [$timestamp] $alert_msg (value: ${alert_val})"
    done
    echo ""
fi

# Performance summary
echo "Performance Summary:"
echo "--------------------"

# Average duration by size bracket
for bracket in "<1MB" "1-10MB" ">10MB"; do
    durations=$(echo "$LOGS" | grep "\"size_bracket\":\"$bracket\"" | grep '"success":true' | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2 || echo "")

    if [[ -n "$durations" ]]; then
        count=$(echo "$durations" | wc -l)
        avg=$(echo "$durations" | awk '{sum+=$1} END {if (NR>0) printf "%.2f", sum/NR; else print "0"}')
        max=$(echo "$durations" | sort -n | tail -1)

        printf "  %-8s: avg=%.2fs, max=%.2fs (n=%d)\n" "$bracket" "$avg" "$max" "$count"
    fi
done

echo ""
echo "==================================================="
echo "✓ Monitoring complete"
echo "==================================================="
