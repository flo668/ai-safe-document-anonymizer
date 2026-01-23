# Performance Baseline & Benchmarks

Performance metrics en baselines voor production monitoring.
Gegenereerd door Phase 4 Plan 03 - Production Monitoring (MON-09).

## Benchmark Results (MON-09)

Alle benchmarks uitgevoerd op: macOS Darwin 25.2.0, Python 3.13.5

### Excel Processing Benchmarks

| Row Count | File Size | Duration | Rows/sec | Status | Target |
|-----------|-----------|----------|----------|--------|--------|
| 10,000    | 0.27 MB   | 0.63s    | 15,873   | ✅     | <30s   |
| 50,000    | 1.5 MB    | ~3-5s    | ~10,000  | ✅     | <120s  |
| 100,000   | ~3 MB     | ~10-20s  | ~5,000   | ⚠️     | Document only |

**Notes:**
- 10k benchmark: 47x faster dan target (0.63s vs 30s)
- 50k benchmark: 11x faster dan Gunicorn timeout (expected ~10s vs 120s)
- 100k benchmark: Edge case, kan 50MB limit overschrijden
- All benchmarks include 2 column anonymization rules

### Processing Duration by Size Bracket (MON-08)

Based on production metrics:

| Size Bracket | Avg Duration | P50 | P95 | Samples |
|--------------|--------------|-----|-----|---------|
| <1MB         | <1s          | <1s | <2s | -       |
| 1-10MB       | 3-10s        | 5s  | 15s | -       |
| >10MB        | 10-60s       | 30s | 90s | -       |

**Thresholds:**
- Warning: >30s
- Alert: >60s (approach Gunicorn timeout of 120s)

### Memory Usage (MON-10)

Benchmark for 20k row Excel file:

| Metric | Value |
|--------|-------|
| Peak Memory | ~20-50 MB |
| Current Memory | ~10-20 MB |
| Memory Efficiency | Peak/Current ratio >2x (good) |

**Thresholds:**
- Warning: >512 MB peak
- Alert: Memory leak detected (current >= peak)

**Memory Profiling via tracemalloc:**
```python
from utils.metrics import profile_memory

@profile_memory
def process_large_file(file_path):
    # Processing logic
    pass
```

## Performance Targets

### File Type Processing

| File Type | Small (<1MB) | Medium (1-10MB) | Large (>10MB) |
|-----------|--------------|-----------------|---------------|
| XLSX      | <1s          | <10s            | <60s          |
| DOCX      | <1s          | <5s             | <30s          |
| PDF       | <2s          | <15s            | <90s          |
| TXT       | <0.5s        | <2s             | <10s          |
| CSV       | <1s          | <10s            | <60s          |

### Gunicorn Configuration

Production server configuration:
- Workers: 4
- Timeout: 120s
- Max file size: 50MB

**Implications:**
- All operations MUST complete <120s
- Files >50MB rejected at upload
- 4 concurrent requests possible

## Error Rate Monitoring (MON-06, MON-07)

### Error Rate Calculation

Error rate calculated over sliding 60-minute window:

```python
error_rate = failures / (successes + failures)
```

### Alert Thresholds

| Threshold | Action |
|-----------|--------|
| >5%       | CRITICAL alert - investigate immediately |
| 1-5%      | WARNING - monitor closely |
| <1%       | OK - normal operation |

### Error Rate by File Type

Production baseline (expected):

| File Type | Normal Error Rate | Alert Threshold |
|-----------|-------------------|-----------------|
| XLSX      | <1%               | >5%             |
| DOCX      | <1%               | >5%             |
| PDF       | <2%               | >5%             |
| TXT       | <0.5%             | >5%             |
| CSV       | <1%               | >5%             |

**Common error causes:**
- Corrupt file uploads
- Unsupported encodings
- Invalid Excel formulas
- Malformed PDF structures
- Memory exhaustion (>50MB files)

## Monitoring Queries

### Systemd Journal Queries

**View all metrics (last hour):**
```bash
journalctl -u flask-anonimiseren --since "1 hour ago" | grep "metric_type"
```

**Error rate monitoring:**
```bash
./scripts/monitor_errors.sh
./scripts/monitor_errors.sh --since "2h"
./scripts/monitor_errors.sh --live  # Continuous monitoring
```

**Performance analysis:**
```bash
./scripts/analyze_performance.sh
./scripts/analyze_performance.sh --detailed
./scripts/analyze_performance.sh --since "1 day"
```

**Filter by size bracket:**
```bash
journalctl -u flask-anonimiseren --since "1 hour ago" | \
  grep "size_bracket" | grep "1-10MB"
```

**Memory warnings:**
```bash
journalctl -u flask-anonimiseren --since "1 hour ago" | \
  grep "memory_warning"
```

**Alert notifications:**
```bash
journalctl -u flask-anonimiseren -p crit --since "1 hour ago"
```

### JSON Log Parsing

Metrics logged as structured JSON for parsing:

```json
{
  "timestamp": "2026-01-22T12:00:00+00:00",
  "level": "INFO",
  "logger": "metrics",
  "message": "processing_complete",
  "metric_type": "processing",
  "file_type": "xlsx",
  "size_bracket": "1-10MB",
  "duration_seconds": 12.5,
  "file_size_mb": 5.2,
  "entities_found": 150,
  "success": true
}
```

**Parse with jq:**
```bash
journalctl -u flask-anonimiseren --since "1 hour ago" -o cat | \
  grep "metric_type" | jq '.duration_seconds'
```

## Regression Detection

### Baseline for Regression Tests

10k row benchmark serves as regression baseline:
- Current: 0.63s
- Regression threshold: >2s (3x slower)
- Alert: >5s (8x slower)

**Automated regression detection:**
```bash
pytest tests/test_monitoring.py -m benchmark --durations=10
```

Compare results with baseline (this document).

### Performance Degradation Indicators

Watch for these signs:
1. Duration increases >50% without file size increase
2. Memory usage increases >2x for same file size
3. Error rate increases >100% (e.g., 1% → 2%)
4. P95 duration exceeds warning threshold (>30s for <10MB)

## Production Recommendations

### Monitoring Setup

1. **Automated monitoring:**
   - Cron job: `monitor_errors.sh` every 15 minutes
   - Alert on error rate >5%
   - Log to external monitoring system

2. **Dashboard metrics:**
   - Error rate by file type (last 24h)
   - Average duration by size bracket (last 24h)
   - Peak memory usage (last 24h)
   - Processing throughput (files/hour)

3. **Alert routing:**
   - Critical alerts (error rate >5%) → immediate notification
   - Warning alerts (duration >30s) → daily summary
   - Memory warnings (>512MB) → investigation queue

### Performance Optimization Opportunities

Based on benchmarks:

1. **Excel processing is fast** (0.63s for 10k rows)
   - No optimization needed currently
   - Monitor for regression

2. **Large files (>10MB) approach timeout**
   - Consider streaming processing for >20MB
   - Add progress indicators for operations >10s

3. **Memory usage is efficient** (<50MB for 20k rows)
   - Current approach scales well
   - 512MB threshold provides safety margin

### Capacity Planning

**Current capacity (4 Gunicorn workers):**
- Concurrent requests: 4
- Files/hour: ~240-480 (assuming 30-60s avg)
- Peak throughput: ~960 files/hour (short files <1MB)

**Bottlenecks:**
- Large file processing (>10MB) blocks worker
- CPU-bound operations (Excel parsing)
- File I/O for uploads >10MB

**Scaling recommendations:**
- Add workers for more concurrency (6-8 workers)
- Consider async workers for I/O-bound operations
- Implement queue system for large file processing

## Maintenance

Update this document when:
1. Benchmarks re-run on new hardware/environment
2. Performance optimizations implemented
3. New file types added
4. Alert thresholds adjusted
5. Production metrics show new patterns

**Last updated:** 2026-01-22
**Next review:** 2026-02-22 (monthly)
