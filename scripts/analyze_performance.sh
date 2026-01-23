#!/bin/bash
#
# Performance Analysis Script
#
# Analyzes processing duration and performance metrics from systemd journal.
# Provides statistics by file type and size bracket.
#
# Usage:
#   ./analyze_performance.sh                 # Analyze last hour
#   ./analyze_performance.sh --since "1 day" # Analyze last day
#   ./analyze_performance.sh --detailed      # Show detailed stats

set -euo pipefail

# Configuration
SERVICE_NAME="flask-anonimiseren"
TIME_WINDOW="${1:---since "1 hour ago"}"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==================================================="
echo "Performance Analyzer - Flask Anonimiseren Tool"
echo "==================================================="
echo ""

# Query logs
echo "📊 Analyzing performance ${TIME_WINDOW}..."
echo ""

# Get processing metrics
LOGS=$(journalctl -u ${SERVICE_NAME} ${TIME_WINDOW} --output=cat 2>/dev/null | grep -E '"metric_type":"processing"' | grep '"success":true' || true)

if [[ -z "$LOGS" ]]; then
    echo -e "${YELLOW}⚠️  No successful processing metrics found in time window${NC}"
    echo "   The service may not be running or no files were processed successfully."
    exit 0
fi

# Total statistics
total_count=$(echo "$LOGS" | wc -l)
echo -e "${GREEN}✓ Found $total_count successful processing operations${NC}"
echo ""

# Performance by Size Bracket
echo "Performance by Size Bracket (MON-08):"
echo "--------------------------------------"

for bracket in "<1MB" "1-10MB" ">10MB"; do
    bracket_logs=$(echo "$LOGS" | grep "\"size_bracket\":\"$bracket\"" || true)

    if [[ -z "$bracket_logs" ]]; then
        continue
    fi

    count=$(echo "$bracket_logs" | wc -l)
    durations=$(echo "$bracket_logs" | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2)

    if [[ -n "$durations" ]]; then
        avg=$(echo "$durations" | awk '{sum+=$1} END {if (NR>0) printf "%.2f", sum/NR; else print "0"}')
        min=$(echo "$durations" | sort -n | head -1)
        max=$(echo "$durations" | sort -n | tail -1)
        p50=$(echo "$durations" | sort -n | awk '{a[NR]=$1} END {print a[int(NR/2)]}')
        p95=$(echo "$durations" | sort -n | awk '{a[NR]=$1} END {print a[int(NR*0.95)]}')

        echo -e "${BLUE}$bracket${NC}"
        printf "  Count:       %d files\n" "$count"
        printf "  Average:     %.2fs\n" "$avg"
        printf "  Min:         %.2fs\n" "$min"
        printf "  Max:         %.2fs\n" "$max"
        printf "  P50 (median): %.2fs\n" "$p50"
        printf "  P95:         %.2fs\n" "$p95"
        echo ""
    fi
done

# Performance by File Type
echo "Performance by File Type:"
echo "-------------------------"

for file_type in xlsx docx pdf txt csv; do
    type_logs=$(echo "$LOGS" | grep "\"file_type\":\"$file_type\"" || true)

    if [[ -z "$type_logs" ]]; then
        continue
    fi

    count=$(echo "$type_logs" | wc -l)
    durations=$(echo "$type_logs" | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2)

    if [[ -n "$durations" ]]; then
        avg=$(echo "$durations" | awk '{sum+=$1} END {if (NR>0) printf "%.2f", sum/NR; else print "0"}')
        max=$(echo "$durations" | sort -n | tail -1)

        printf "  %-6s: avg=%.2fs, max=%.2fs (n=%d)\n" "$file_type" "$avg" "$max" "$count"
    fi
done

echo ""

# Entity detection stats
echo "Entity Detection Stats:"
echo "-----------------------"

entities=$(echo "$LOGS" | grep -oP '"entities_found":[0-9]+' | cut -d':' -f2)

if [[ -n "$entities" ]]; then
    total_entities=$(echo "$entities" | awk '{sum+=$1} END {print sum}')
    avg_entities=$(echo "$entities" | awk '{sum+=$1} END {if (NR>0) printf "%.1f", sum/NR; else print "0"}')
    max_entities=$(echo "$entities" | sort -n | tail -1)

    echo "  Total entities detected:  $total_entities"
    echo "  Average per file:         $avg_entities"
    echo "  Max in single file:       $max_entities"
    echo ""
fi

# Memory usage stats (if available)
MEMORY_LOGS=$(journalctl -u ${SERVICE_NAME} ${TIME_WINDOW} --output=cat 2>/dev/null | grep -E '"metric_type":"memory"' || true)

if [[ -n "$MEMORY_LOGS" ]]; then
    echo "Memory Usage Stats:"
    echo "-------------------"

    peak_memories=$(echo "$MEMORY_LOGS" | grep -oP '"memory_peak_mb":[0-9.]+' | cut -d':' -f2)

    if [[ -n "$peak_memories" ]]; then
        avg_peak=$(echo "$peak_memories" | awk '{sum+=$1} END {if (NR>0) printf "%.1f", sum/NR; else print "0"}')
        max_peak=$(echo "$peak_memories" | sort -n | tail -1)

        echo "  Average peak:  ${avg_peak}MB"
        echo "  Max peak:      ${max_peak}MB"
        echo ""
    fi
fi

# Slowest operations (if detailed flag)
if [[ "${1:-}" == "--detailed" ]]; then
    echo "Top 10 Slowest Operations:"
    echo "--------------------------"

    echo "$LOGS" | while read -r line; do
        duration=$(echo "$line" | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2 || echo "0")
        file_type=$(echo "$line" | grep -oP '"file_type":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        size_mb=$(echo "$line" | grep -oP '"file_size_mb":[0-9.]+' | cut -d':' -f2 || echo "0")
        entities=$(echo "$line" | grep -oP '"entities_found":[0-9]+' | cut -d':' -f2 || echo "0")

        printf "%.2f\t%s\t%.2f\t%s\n" "$duration" "$file_type" "$size_mb" "$entities"
    done | sort -rn | head -10 | while read -r duration file_type size_mb entities; do
        printf "  %.2fs - %s (%.2fMB, %s entities)\n" "$duration" "$file_type" "$size_mb" "$entities"
    done

    echo ""
fi

# Warnings and recommendations
echo "Warnings & Recommendations:"
echo "---------------------------"

slow_count=$(echo "$LOGS" | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2 | awk '$1 > 30 {count++} END {print count+0}')
very_slow_count=$(echo "$LOGS" | grep -oP '"duration_seconds":[0-9.]+' | cut -d':' -f2 | awk '$1 > 60 {count++} END {print count+0}')

if [[ "$very_slow_count" -gt 0 ]]; then
    echo -e "  ${YELLOW}⚠️  $very_slow_count operations took >60s (alert threshold)${NC}"
    echo "     Consider optimizing processing for large files"
elif [[ "$slow_count" -gt 0 ]]; then
    echo -e "  ${YELLOW}⚠️  $slow_count operations took >30s (warning threshold)${NC}"
    echo "     Monitor for potential performance issues"
else
    echo -e "  ${GREEN}✓  All operations completed within acceptable time${NC}"
fi

echo ""
echo "==================================================="
echo "✓ Analysis complete"
echo "==================================================="
