"""
Production Monitoring & Performance Profiling Tests

Tests voor MON-06 tot MON-10:
- Error rate monitoring
- Processing duration logging
- Performance profiling benchmarks (10k, 50k, 100k rows)
- Memory usage monitoring

Performance benchmarks worden gemarkeerd met @pytest.mark.benchmark
en @pytest.mark.slow voor selectieve uitvoering.

Run benchmarks:
    pytest tests/test_monitoring.py -v -m benchmark --durations=10
"""

import pytest
import time
import tracemalloc
from pathlib import Path
from openpyxl import Workbook
from utils.metrics import MetricsCollector, get_metrics_collector, profile_memory


class TestMetricsCollector:
    """Test suite voor MetricsCollector class."""

    def test_size_bracket_classification(self):
        """Test file size bracket classification."""
        # <1MB
        assert MetricsCollector.get_size_bracket(500 * 1024) == '<1MB'
        assert MetricsCollector.get_size_bracket(1024 * 1024 - 1) == '<1MB'

        # 1-10MB
        assert MetricsCollector.get_size_bracket(1024 * 1024) == '1-10MB'
        assert MetricsCollector.get_size_bracket(5 * 1024 * 1024) == '1-10MB'
        assert MetricsCollector.get_size_bracket(10 * 1024 * 1024 - 1) == '1-10MB'

        # >10MB
        assert MetricsCollector.get_size_bracket(10 * 1024 * 1024) == '>10MB'
        assert MetricsCollector.get_size_bracket(50 * 1024 * 1024) == '>10MB'

    def test_log_processing_metrics_success(self, tmp_path):
        """Test logging successful processing metrics."""
        metrics = MetricsCollector()

        # Log successful processing
        metrics.log_processing_metrics(
            file_type='xlsx',
            file_size=5 * 1024 * 1024,  # 5MB
            duration=12.5,
            entities_found=150,
            success=True
        )

        # Verify metrics stored in history
        assert 'xlsx' in metrics._metrics_history
        assert len(metrics._metrics_history['xlsx']) == 1

        metric = metrics._metrics_history['xlsx'][0]
        assert metric['success'] is True
        assert metric['duration'] == 12.5
        assert metric['size_bracket'] == '1-10MB'

    def test_log_processing_metrics_failure(self):
        """Test logging failed processing metrics."""
        metrics = MetricsCollector()

        # Log failed processing
        metrics.log_processing_metrics(
            file_type='docx',
            file_size=2 * 1024 * 1024,
            duration=3.2,
            entities_found=0,
            success=False,
            error='File corrupted'
        )

        # Verify metrics stored
        assert 'docx' in metrics._metrics_history
        metric = metrics._metrics_history['docx'][0]
        assert metric['success'] is False

    def test_error_rate_calculation_no_data(self):
        """Test error rate calculation with no data."""
        metrics = MetricsCollector()
        error_rate = metrics.get_error_rate('xlsx', window_minutes=60)
        assert error_rate == 0.0

    def test_error_rate_calculation_all_success(self):
        """Test error rate with all successful operations."""
        metrics = MetricsCollector()

        # Log 5 successful operations
        for i in range(5):
            metrics.log_processing_metrics(
                file_type='xlsx',
                file_size=1024 * 1024,
                duration=1.0,
                entities_found=10,
                success=True
            )

        error_rate = metrics.get_error_rate('xlsx', window_minutes=60)
        assert error_rate == 0.0

    def test_error_rate_calculation_with_failures(self):
        """Test error rate with some failures (MON-06)."""
        metrics = MetricsCollector()

        # Log 8 successful, 2 failed (20% error rate)
        for i in range(8):
            metrics.log_processing_metrics(
                file_type='xlsx',
                file_size=1024 * 1024,
                duration=1.0,
                entities_found=10,
                success=True
            )

        for i in range(2):
            metrics.log_processing_metrics(
                file_type='xlsx',
                file_size=1024 * 1024,
                duration=1.0,
                entities_found=0,
                success=False,
                error='Test error'
            )

        error_rate = metrics.get_error_rate('xlsx', window_minutes=60)
        assert error_rate == 0.2  # 2/10 = 20%

    def test_error_rate_alert_threshold(self):
        """Test alert trigger when error rate exceeds 5% (MON-07)."""
        metrics = MetricsCollector()

        # Create 94 successful, 6 failed (6% error rate > 5% threshold)
        for i in range(94):
            metrics.log_processing_metrics(
                file_type='pdf',
                file_size=1024 * 1024,
                duration=1.0,
                entities_found=10,
                success=True
            )

        for i in range(6):
            metrics.log_processing_metrics(
                file_type='pdf',
                file_size=1024 * 1024,
                duration=1.0,
                entities_found=0,
                success=False,
                error='Test error'
            )

        error_rate = metrics.get_error_rate('pdf', window_minutes=60)
        assert error_rate == 0.06  # 6/100 = 6%

        # Should trigger alert (>5%)
        assert error_rate > metrics.ERROR_RATE_THRESHOLD

    def test_processing_stats_by_size_bracket(self):
        """Test duration statistics per size bracket (MON-08)."""
        metrics = MetricsCollector()

        # Log operations in different size brackets
        # <1MB: 2 operations (2s, 3s)
        metrics.log_processing_metrics('xlsx', 500 * 1024, 2.0, 10, True)
        metrics.log_processing_metrics('xlsx', 800 * 1024, 3.0, 15, True)

        # 1-10MB: 3 operations (5s, 6s, 7s)
        metrics.log_processing_metrics('xlsx', 2 * 1024 * 1024, 5.0, 20, True)
        metrics.log_processing_metrics('xlsx', 5 * 1024 * 1024, 6.0, 25, True)
        metrics.log_processing_metrics('xlsx', 8 * 1024 * 1024, 7.0, 30, True)

        # Get stats for 1-10MB bracket
        stats = metrics.get_processing_stats('1-10MB')

        assert stats['count'] == 3
        assert stats['avg_duration'] == 6.0  # (5+6+7)/3
        assert stats['min_duration'] == 5.0
        assert stats['max_duration'] == 7.0

    def test_memory_metrics_logging(self):
        """Test memory usage logging (MON-10)."""
        metrics = MetricsCollector()

        # Log memory metrics
        peak_memory = 128 * 1024 * 1024  # 128MB
        current_memory = 64 * 1024 * 1024  # 64MB

        # Should not raise exception
        metrics.log_memory_metrics(
            operation='test_operation',
            peak_memory=peak_memory,
            current_memory=current_memory
        )

    def test_global_metrics_singleton(self):
        """Test global metrics collector singleton."""
        metrics1 = get_metrics_collector()
        metrics2 = get_metrics_collector()

        # Should be same instance
        assert metrics1 is metrics2


class TestMemoryProfiling:
    """Test suite voor memory profiling decorator."""

    def test_profile_memory_decorator(self):
        """Test memory profiling decorator (MON-10)."""

        @profile_memory
        def allocate_memory():
            # Allocate ~10MB
            data = [0] * (10 * 1024 * 1024 // 8)
            return len(data)

        # Should execute without error and log memory usage
        result = allocate_memory()
        assert result > 0


# ===================================================================
# Performance Profiling Benchmarks (MON-09)
# ===================================================================

def create_excel_with_rows(num_rows: int, tmp_path: Path) -> Path:
    """
    Helper: Create Excel file with specified number of rows.

    Args:
        num_rows: Number of data rows (excluding header)
        tmp_path: Temporary directory path

    Returns:
        Path to created Excel file
    """
    filepath = tmp_path / f"benchmark_{num_rows}.xlsx"

    wb = Workbook()
    ws = wb.active

    # Header
    ws.append(['Naam', 'Email', 'Telefoon', 'Adres', 'Postcode'])

    # Data rows
    for i in range(num_rows):
        ws.append([
            f'Gebruiker_{i}',
            f'user{i}@example.com',
            f'06-{12345678 + i}',
            f'Straat {i}, Amsterdam',
            f'1000AA'
        ])

    wb.save(filepath)
    return filepath


@pytest.mark.slow
@pytest.mark.benchmark
def test_profile_10k_rows(tmp_path):
    """
    Benchmark 10k row Excel processing (MON-09).

    Target: <30s
    Expected: ~2-5s based on Phase 4 Plan 02 results (1.78s for 10k)
    """
    from anonymizer.excel_anonymizer import ExcelAnonymizer, ExcelColumnRule

    # Create test file
    filepath = create_excel_with_rows(10_000, tmp_path)

    # Prepare rules using ExcelColumnRule
    rules = [
        ExcelColumnRule({
            'columnName': 'Email',
            'anonymizationType': 'replace',
            'replaceWith': '[EMAIL VERWIJDERD]',
            'columnType': 'text'
        }),
        ExcelColumnRule({
            'columnName': 'Telefoon',
            'anonymizationType': 'replace',
            'replaceWith': '[TEL VERWIJDERD]',
            'columnType': 'text'
        })
    ]

    output_path = tmp_path / "output_10k.xlsx"

    # Benchmark processing
    start = time.time()

    ExcelAnonymizer.process_excel_file(
        filepath,
        output_path,
        rules,
        preserve_headers=True
    )

    duration = time.time() - start

    # Log results
    print(f"\n10k rows: {duration:.2f}s")

    # Verify performance
    assert duration < 30, f"Too slow: {duration:.2f}s (target: <30s)"

    # Verify output exists
    assert output_path.exists()

    # Log metrics
    metrics = get_metrics_collector()
    metrics.log_processing_metrics(
        file_type='xlsx',
        file_size=filepath.stat().st_size,
        duration=duration,
        entities_found=20_000,  # 2 columns × 10k rows
        success=True
    )


@pytest.mark.slow
@pytest.mark.benchmark
def test_profile_50k_rows(tmp_path):
    """
    Benchmark 50k row Excel processing (MON-09).

    Target: <120s (Gunicorn timeout)
    Expected: ~10-15s based on Phase 4 Plan 02 results (10.4s for 50k)
    """
    from anonymizer.excel_anonymizer import ExcelAnonymizer, ExcelColumnRule

    # Create test file
    filepath = create_excel_with_rows(50_000, tmp_path)

    # Prepare rules
    rules = [
        ExcelColumnRule({
            'columnName': 'Email',
            'anonymizationType': 'replace',
            'replaceWith': '[EMAIL VERWIJDERD]',
            'columnType': 'text'
        })
    ]

    output_path = tmp_path / "output_50k.xlsx"

    # Benchmark processing
    start = time.time()

    ExcelAnonymizer.process_excel_file(
        filepath,
        output_path,
        rules,
        preserve_headers=True
    )

    duration = time.time() - start

    # Log results
    print(f"\n50k rows: {duration:.2f}s")

    # Verify performance
    assert duration < 120, f"Exceeds Gunicorn timeout: {duration:.2f}s (target: <120s)"

    # Verify output exists
    assert output_path.exists()

    # Log metrics
    metrics = get_metrics_collector()
    metrics.log_processing_metrics(
        file_type='xlsx',
        file_size=filepath.stat().st_size,
        duration=duration,
        entities_found=50_000,
        success=True
    )


@pytest.mark.slow
@pytest.mark.benchmark
def test_profile_100k_rows(tmp_path):
    """
    Benchmark 100k row Excel processing (MON-09).

    This is an edge case - may exceed 50MB limit or timeout.
    Documents baseline performance for very large files.

    Expected: ~20-40s or may fail due to size limit
    """
    from anonymizer.excel_anonymizer import ExcelAnonymizer, ExcelColumnRule

    # Create test file
    filepath = create_excel_with_rows(100_000, tmp_path)

    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"\n100k rows file size: {file_size_mb:.2f}MB")

    # May skip if file exceeds 50MB limit
    if file_size_mb > 50:
        pytest.skip(f"File exceeds 50MB limit: {file_size_mb:.2f}MB")

    # Prepare rules
    rules = [
        ExcelColumnRule({
            'columnName': 'Email',
            'anonymizationType': 'replace',
            'replaceWith': '[EMAIL VERWIJDERD]',
            'columnType': 'text'
        })
    ]

    output_path = tmp_path / "output_100k.xlsx"

    # Benchmark processing
    start = time.time()

    ExcelAnonymizer.process_excel_file(
        filepath,
        output_path,
        rules,
        preserve_headers=True
    )

    duration = time.time() - start

    # Log results
    print(f"\n100k rows: {duration:.2f}s")
    print(f"Performance: {100_000 / duration:.0f} rows/second")

    # Document performance (no hard limit, just baseline)
    # This serves as regression detection baseline

    # Verify output exists
    assert output_path.exists()

    # Log metrics
    metrics = get_metrics_collector()
    metrics.log_processing_metrics(
        file_type='xlsx',
        file_size=filepath.stat().st_size,
        duration=duration,
        entities_found=100_000,
        success=True
    )


@pytest.mark.slow
@pytest.mark.benchmark
def test_profile_memory_during_large_file(tmp_path):
    """
    Test memory usage during large file processing (MON-10).

    Tracks peak memory usage to ensure no memory leaks.
    """
    from anonymizer.excel_anonymizer import ExcelAnonymizer, ExcelColumnRule

    # Create 20k row file (~moderate size)
    filepath = create_excel_with_rows(20_000, tmp_path)

    rules = [
        ExcelColumnRule({
            'columnName': 'Email',
            'anonymizationType': 'replace',
            'replaceWith': '[EMAIL]',
            'columnType': 'text'
        })
    ]

    output_path = tmp_path / "output_memory_test.xlsx"

    # Track memory
    tracemalloc.start()

    ExcelAnonymizer.process_excel_file(
        filepath,
        output_path,
        rules,
        preserve_headers=True
    )

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Log memory usage
    metrics = get_metrics_collector()
    metrics.log_memory_metrics(
        operation='excel_20k_rows',
        peak_memory=peak,
        current_memory=current
    )

    # Report
    print(f"\nMemory usage for 20k rows:")
    print(f"  Peak: {peak / 1024 / 1024:.1f}MB")
    print(f"  Current: {current / 1024 / 1024:.1f}MB")

    # Verify no memory leak (current should be much lower than peak)
    assert current < peak, "Possible memory leak: current >= peak"

    # Verify reasonable memory usage (<512MB warning threshold)
    peak_mb = peak / 1024 / 1024
    if peak_mb > 512:
        print(f"WARNING: High memory usage: {peak_mb:.1f}MB")


@pytest.mark.benchmark
def test_duration_logging_per_size_bracket(tmp_path):
    """
    Test that processing duration is logged per size bracket (MON-08).

    Verifies that metrics are correctly categorized by file size.
    """
    from anonymizer.excel_anonymizer import ExcelAnonymizer, ExcelColumnRule
    metrics = get_metrics_collector()

    # Small file (<1MB)
    small_file = create_excel_with_rows(100, tmp_path)
    small_rules = [
        ExcelColumnRule({
            'columnName': 'Email',
            'anonymizationType': 'replace',
            'replaceWith': '[EMAIL]',
            'columnType': 'text'
        })
    ]
    small_output = tmp_path / "small_output.xlsx"

    start = time.time()
    ExcelAnonymizer.process_excel_file(
        small_file,
        small_output,
        small_rules,
        preserve_headers=True
    )
    duration = time.time() - start

    metrics.log_processing_metrics(
        file_type='xlsx',
        file_size=small_file.stat().st_size,
        duration=duration,
        entities_found=100,
        success=True
    )

    # Verify size bracket classification
    assert MetricsCollector.get_size_bracket(small_file.stat().st_size) == '<1MB'

    # Get stats for <1MB bracket
    stats = metrics.get_processing_stats('<1MB')
    assert stats['count'] >= 1

    print(f"\n<1MB bracket stats: avg={stats['avg_duration']:.2f}s, count={stats['count']}")
