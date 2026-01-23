"""
Production Monitoring & Metrics Collection

Verzamelt en logt processing metrics voor production reliability monitoring.
Ondersteunt error rate tracking, duration logging, en performance profiling.

Integreert met bestaande AuditLogger voor GDPR-compliant logging.
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from collections import defaultdict
import tracemalloc


class MetricsCollector:
    """
    Collect and log processing metrics for production monitoring.

    Tracks:
    - Processing duration per file type and size bracket
    - Error rates per file type
    - Entity detection counts
    - Memory usage during processing

    Logs structured JSON to systemd journal for parsing by monitoring tools.

    Usage:
        metrics = MetricsCollector()

        # Log processing metrics
        metrics.log_processing_metrics(
            file_type='xlsx',
            file_size=5_242_880,  # 5MB
            duration=12.5,
            entities_found=150,
            success=True
        )

        # Check error rates
        error_rate = metrics.get_error_rate('xlsx', window_minutes=60)
        if error_rate > 0.05:
            metrics.trigger_alert('High error rate for xlsx', error_rate)
    """

    # File size brackets (bytes)
    SIZE_BRACKET_SMALL = 1024 * 1024  # <1MB
    SIZE_BRACKET_MEDIUM = 10 * 1024 * 1024  # <10MB
    # >10MB is large

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.05  # 5%
    DURATION_WARNING_THRESHOLD = 30  # seconds
    DURATION_ALERT_THRESHOLD = 60  # seconds
    MEMORY_WARNING_THRESHOLD = 512 * 1024 * 1024  # 512MB

    def __init__(self):
        """Initialize metrics collector."""
        self.logger = self._setup_logger()

        # In-memory metrics storage (last 24h)
        # Structure: {'xlsx': [{'timestamp': ..., 'success': True, 'duration': 5.2}, ...]}
        self._metrics_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def _setup_logger(self) -> logging.Logger:
        """
        Setup structured logging for metrics.

        Logs to:
        1. Systemd journal (production) - structured JSON format
        2. Console (development) - human-readable format

        Returns:
            Configured Logger instance
        """
        logger = logging.getLogger('metrics')
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        logger.handlers.clear()

        # Console handler (fallback)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Structured JSON formatter voor systemd journal parsing
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                # Build structured log
                log_obj = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage()
                }

                # Add extra fields from record
                if hasattr(record, 'metric_type'):
                    log_obj['metric_type'] = record.metric_type
                if hasattr(record, 'file_type'):
                    log_obj['file_type'] = record.file_type
                if hasattr(record, 'size_bracket'):
                    log_obj['size_bracket'] = record.size_bracket
                if hasattr(record, 'duration_seconds'):
                    log_obj['duration_seconds'] = record.duration_seconds
                if hasattr(record, 'file_size_mb'):
                    log_obj['file_size_mb'] = record.file_size_mb
                if hasattr(record, 'entities_found'):
                    log_obj['entities_found'] = record.entities_found
                if hasattr(record, 'success'):
                    log_obj['success'] = record.success
                if hasattr(record, 'error'):
                    log_obj['error'] = record.error
                if hasattr(record, 'error_rate'):
                    log_obj['error_rate'] = record.error_rate
                if hasattr(record, 'memory_peak_mb'):
                    log_obj['memory_peak_mb'] = record.memory_peak_mb
                if hasattr(record, 'memory_current_mb'):
                    log_obj['memory_current_mb'] = record.memory_current_mb

                return json.dumps(log_obj)

        console_handler.setFormatter(StructuredFormatter())
        logger.addHandler(console_handler)

        # Don't propagate to root logger
        logger.propagate = False

        return logger

    @staticmethod
    def get_size_bracket(file_size: int) -> str:
        """
        Classify file size into bracket.

        Args:
            file_size: File size in bytes

        Returns:
            Size bracket string: '<1MB', '1-10MB', or '>10MB'
        """
        if file_size < MetricsCollector.SIZE_BRACKET_SMALL:
            return '<1MB'
        elif file_size < MetricsCollector.SIZE_BRACKET_MEDIUM:
            return '1-10MB'
        else:
            return '>10MB'

    def log_processing_metrics(
        self,
        file_type: str,
        file_size: int,
        duration: float,
        entities_found: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Log metrics for a processing operation.

        Args:
            file_type: File type (xlsx, docx, pdf, txt, csv)
            file_size: File size in bytes
            duration: Processing duration in seconds
            entities_found: Number of entities detected/replaced
            success: Whether processing succeeded
            error: Error message if failed
        """
        size_bracket = self.get_size_bracket(file_size)
        file_size_mb = file_size / (1024 * 1024)

        # Log structured metrics
        self.logger.info(
            f"processing_{'complete' if success else 'error'}",
            extra={
                'metric_type': 'processing',
                'file_type': file_type,
                'size_bracket': size_bracket,
                'duration_seconds': round(duration, 2),
                'file_size_mb': round(file_size_mb, 2),
                'entities_found': entities_found,
                'success': success,
                'error': error
            }
        )

        # Store in memory for error rate calculation
        metric_entry = {
            'timestamp': datetime.now(timezone.utc),
            'success': success,
            'duration': duration,
            'size_bracket': size_bracket,
            'file_size': file_size
        }
        self._metrics_history[file_type].append(metric_entry)

        # Cleanup old metrics (>24h)
        self._cleanup_old_metrics(file_type)

        # Check duration thresholds
        if duration > self.DURATION_ALERT_THRESHOLD:
            self.trigger_alert(
                f"Processing duration exceeded {self.DURATION_ALERT_THRESHOLD}s",
                duration,
                file_type=file_type,
                size_bracket=size_bracket
            )
        elif duration > self.DURATION_WARNING_THRESHOLD:
            self.logger.warning(
                f"processing_slow",
                extra={
                    'metric_type': 'duration_warning',
                    'file_type': file_type,
                    'size_bracket': size_bracket,
                    'duration_seconds': round(duration, 2)
                }
            )

    def log_memory_metrics(
        self,
        operation: str,
        peak_memory: int,
        current_memory: int
    ) -> None:
        """
        Log memory usage metrics.

        Args:
            operation: Operation description
            peak_memory: Peak memory usage in bytes
            current_memory: Current memory usage in bytes
        """
        peak_mb = peak_memory / (1024 * 1024)
        current_mb = current_memory / (1024 * 1024)

        self.logger.info(
            f"memory_usage",
            extra={
                'metric_type': 'memory',
                'operation': operation,
                'memory_peak_mb': round(peak_mb, 1),
                'memory_current_mb': round(current_mb, 1)
            }
        )

        # Check memory threshold
        if peak_memory > self.MEMORY_WARNING_THRESHOLD:
            self.logger.warning(
                f"high_memory_usage",
                extra={
                    'metric_type': 'memory_warning',
                    'operation': operation,
                    'memory_peak_mb': round(peak_mb, 1)
                }
            )

    def get_error_rate(self, file_type: str, window_minutes: int = 60) -> float:
        """
        Calculate error rate for file type in time window.

        Args:
            file_type: File type to check (xlsx, docx, pdf, txt, csv)
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Error rate as float (0.0 to 1.0), or 0.0 if no data
        """
        if file_type not in self._metrics_history:
            return 0.0

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        # Filter metrics in time window
        recent_metrics = [
            m for m in self._metrics_history[file_type]
            if m['timestamp'] > cutoff_time
        ]

        if not recent_metrics:
            return 0.0

        total = len(recent_metrics)
        failures = sum(1 for m in recent_metrics if not m['success'])

        return failures / total if total > 0 else 0.0

    def get_processing_stats(self, size_bracket: str) -> Dict[str, float]:
        """
        Get duration statistics for file size bracket.

        Args:
            size_bracket: Size bracket ('<1MB', '1-10MB', '>10MB')

        Returns:
            Dict with 'avg_duration', 'min_duration', 'max_duration', 'count'
        """
        # Collect all durations for this size bracket across all file types
        durations = []
        for file_type, metrics in self._metrics_history.items():
            for m in metrics:
                if m.get('size_bracket') == size_bracket and m.get('success'):
                    durations.append(m['duration'])

        if not durations:
            return {
                'avg_duration': 0.0,
                'min_duration': 0.0,
                'max_duration': 0.0,
                'count': 0
            }

        return {
            'avg_duration': round(sum(durations) / len(durations), 2),
            'min_duration': round(min(durations), 2),
            'max_duration': round(max(durations), 2),
            'count': len(durations)
        }

    def trigger_alert(
        self,
        message: str,
        value: float,
        file_type: Optional[str] = None,
        size_bracket: Optional[str] = None
    ) -> None:
        """
        Trigger alert (log with CRITICAL level for systemd).

        Args:
            message: Alert message
            value: Metric value that triggered alert
            file_type: File type (optional)
            size_bracket: Size bracket (optional)
        """
        extra = {
            'metric_type': 'alert',
            'alert_message': message,
            'alert_value': round(value, 3)
        }

        if file_type:
            extra['file_type'] = file_type
        if size_bracket:
            extra['size_bracket'] = size_bracket

        self.logger.critical(
            f"ALERT: {message} (value: {value:.3f})",
            extra=extra
        )

    def _cleanup_old_metrics(self, file_type: str) -> None:
        """
        Remove metrics older than 24 hours.

        Args:
            file_type: File type to cleanup
        """
        if file_type not in self._metrics_history:
            return

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        self._metrics_history[file_type] = [
            m for m in self._metrics_history[file_type]
            if m['timestamp'] > cutoff_time
        ]


def profile_memory(func):
    """
    Decorator for memory profiling.

    Tracks peak and current memory usage during function execution.
    Logs metrics via MetricsCollector.

    Usage:
        @profile_memory
        def process_large_file(file_path):
            # ... processing logic
    """
    def wrapper(*args, **kwargs):
        tracemalloc.start()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Log memory metrics
            metrics = MetricsCollector()
            metrics.log_memory_metrics(
                operation=func.__name__,
                peak_memory=peak,
                current_memory=current
            )

    return wrapper


class MemoryProfiler:
    """
    Context manager for memory profiling.

    Tracks memory usage during a block of code.

    Usage:
        with MemoryProfiler('large_file_processing') as profiler:
            # ... processing logic

        print(f"Peak: {profiler.peak_mb:.1f}MB")
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.peak_memory = 0
        self.current_memory = 0
        self.peak_mb = 0.0
        self.current_mb = 0.0

    def __enter__(self):
        tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.current_memory, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.peak_mb = self.peak_memory / (1024 * 1024)
        self.current_mb = self.current_memory / (1024 * 1024)

        # Log memory metrics
        metrics = get_metrics_collector()
        metrics.log_memory_metrics(
            operation=self.operation_name,
            peak_memory=self.peak_memory,
            current_memory=self.current_memory
        )


# Global metrics instance for import convenience
_global_metrics = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global MetricsCollector instance (singleton pattern).

    Returns:
        MetricsCollector instance
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics
