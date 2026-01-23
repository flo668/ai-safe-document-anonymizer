"""
Tests for Pattern Registry and 3-Layer Validation
"""

import pytest
import json
import tempfile
from pathlib import Path
from anonymizer.patterns import (
    PatternRegistry,
    ThreeLayerValidator,
    find_context_words,
    get_detection_summary
)


class TestPatternRegistry:
    """Tests for PatternRegistry class."""

    def test_registry_loads_from_json(self):
        """Test that registry loads correctly from JSON file."""
        registry = PatternRegistry()
        assert registry.config is not None
        assert 'version' in registry.config
        assert 'patterns' in registry.config
        assert registry.config['version'] == '1.0'

    def test_get_enabled_patterns(self):
        """Test getting all enabled patterns."""
        registry = PatternRegistry()
        enabled = registry.get_enabled_patterns()

        # Should have at least phone, email, bsn, iban, postal_code_nl
        assert len(enabled) >= 5
        assert 'phone_nl' in enabled
        assert 'email' in enabled
        assert 'bsn' in enabled
        assert 'iban' in enabled
        assert 'postal_code_nl' in enabled

    def test_get_detector_function(self):
        """Test getting detector functions by name."""
        registry = PatternRegistry()

        # Test phone detector
        phone_detector = registry.get_detector_function('phone_nl')
        assert phone_detector is not None
        assert callable(phone_detector)

        # Test email detector
        email_detector = registry.get_detector_function('email')
        assert email_detector is not None
        assert callable(email_detector)

        # Test BSN detector
        bsn_detector = registry.get_detector_function('bsn')
        assert bsn_detector is not None
        assert callable(bsn_detector)

    def test_get_context_words(self):
        """Test getting context words for patterns."""
        registry = PatternRegistry()

        # Phone context words
        phone_context = registry.get_context_words('phone_nl')
        assert isinstance(phone_context, list)
        assert len(phone_context) > 0
        assert 'telefoon' in phone_context or 'phone' in phone_context

        # BSN context words
        bsn_context = registry.get_context_words('bsn')
        assert isinstance(bsn_context, list)
        assert 'burgerservicenummer' in bsn_context or 'bsn' in bsn_context

    def test_get_confidence_boost(self):
        """Test getting confidence boost values."""
        registry = PatternRegistry()

        # All patterns should have confidence boosts
        for pattern_name in ['phone_nl', 'email', 'bsn', 'iban', 'postal_code_nl']:
            boost = registry.get_confidence_boost(pattern_name)
            assert isinstance(boost, (int, float))
            assert 0.0 <= boost <= 1.0

    def test_registry_with_custom_path(self):
        """Test registry with custom JSON path."""
        # Create temporary JSON file
        custom_config = {
            "version": "1.0",
            "patterns": {
                "test_pattern": {
                    "enabled": True,
                    "description": "Test pattern",
                    "context_words": ["test"],
                    "confidence_boost": 0.5,
                    "detector_function": "detect_phones"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_path = f.name

        try:
            registry = PatternRegistry(registry_path=temp_path)
            enabled = registry.get_enabled_patterns()
            assert 'test_pattern' in enabled
            assert registry.get_confidence_boost('test_pattern') == 0.5
        finally:
            Path(temp_path).unlink()


class TestContextWordDetection:
    """Tests for context word detection."""

    def test_find_context_words_basic(self):
        """Test finding context words within window."""
        text = "Mijn burgerservicenummer is 123456782"
        match_position = text.find("123456782")
        context_words = ["burgerservicenummer", "bsn"]

        count = find_context_words(text, match_position, context_words, window=50)
        assert count >= 1  # Should find "burgerservicenummer"

    def test_find_context_words_no_match(self):
        """Test context word detection when no words present."""
        text = "Random number: 123456782"
        match_position = text.find("123456782")
        context_words = ["burgerservicenummer", "bsn"]

        count = find_context_words(text, match_position, context_words, window=50)
        assert count == 0

    def test_find_context_words_window_boundary(self):
        """Test context words outside window are not detected."""
        text = "burgerservicenummer" + " " * 100 + "123456782"
        match_position = text.find("123456782")
        context_words = ["burgerservicenummer"]

        # Window of 50 chars should not reach "burgerservicenummer"
        count = find_context_words(text, match_position, context_words, window=50)
        assert count == 0

    def test_find_context_words_case_insensitive(self):
        """Test context word detection is case insensitive."""
        text = "Mijn BURGERSERVICENUMMER is 123456782"
        match_position = text.find("123456782")
        context_words = ["burgerservicenummer"]

        count = find_context_words(text, match_position, context_words, window=50)
        assert count >= 1


class TestThreeLayerValidator:
    """Tests for 3-layer validation engine."""

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = ThreeLayerValidator()
        assert validator.registry is not None

    def test_detect_all_phone(self):
        """Test detecting phone numbers with validation."""
        validator = ThreeLayerValidator()
        text = "Bel me op 06-12345678"

        results = validator.detect_all(text)
        assert 'phone_nl' in results
        assert len(results['phone_nl']) > 0

        # Check confidence score
        match, confidence = results['phone_nl'][0]
        assert '06' in match or '6' in match
        assert 0.0 <= confidence <= 1.0

    def test_detect_all_email(self):
        """Test detecting email addresses."""
        validator = ThreeLayerValidator()
        text = "Stuur een email naar test@example.com"

        results = validator.detect_all(text)
        assert 'email' in results
        assert len(results['email']) > 0

        match, confidence = results['email'][0]
        assert match == "test@example.com"
        assert 0.0 <= confidence <= 1.0

    def test_detect_all_bsn(self):
        """Test detecting BSN with checksum validation."""
        validator = ThreeLayerValidator()
        text = "BSN: 123456782"  # Valid BSN

        results = validator.detect_all(text)
        assert 'bsn' in results
        assert len(results['bsn']) > 0

        match, confidence = results['bsn'][0]
        assert match == "123456782"
        assert confidence == 1.0  # Valid checksum

    def test_context_boosting_applied(self):
        """Test that context words boost confidence."""
        validator = ThreeLayerValidator()

        # Text with context word
        text_with_context = "Mijn burgerservicenummer is 123456782"
        results_with = validator.detect_all(text_with_context)

        # Text without context word
        text_without_context = "Nummer: 123456782"
        results_without = validator.detect_all(text_without_context)

        # Both should detect BSN
        assert 'bsn' in results_with
        assert 'bsn' in results_without

        # Context version should have higher or equal confidence
        conf_with = results_with['bsn'][0][1] if results_with['bsn'] else 0
        conf_without = results_without['bsn'][0][1] if results_without['bsn'] else 0

        assert conf_with >= conf_without

    def test_multiple_pattern_detection(self):
        """Test detecting multiple pattern types in same text."""
        validator = ThreeLayerValidator()
        text = """
        Contactgegevens:
        Telefoon: 06-12345678
        Email: contact@example.com
        BSN: 123456782
        IBAN: NL91ABNA0417164300
        Postcode: 1012JS
        """

        results = validator.detect_all(text)

        # Should detect multiple types
        assert 'phone_nl' in results and len(results['phone_nl']) > 0
        assert 'email' in results and len(results['email']) > 0
        assert 'bsn' in results and len(results['bsn']) > 0
        assert 'iban' in results and len(results['iban']) > 0
        assert 'postal_code_nl' in results and len(results['postal_code_nl']) > 0


class TestDetectionSummary:
    """Tests for detection summary statistics."""

    def test_get_detection_summary_empty(self):
        """Test summary with no results."""
        results = {}
        summary = get_detection_summary(results)

        assert summary['total_matches'] == 0
        assert summary['by_type'] == {}
        assert summary['avg_confidence'] == 0.0
        assert summary['high_confidence'] == 0

    def test_get_detection_summary_single_type(self):
        """Test summary with single pattern type."""
        results = {
            'phone_nl': [
                ('06-12345678', 0.95),
                ('06-87654321', 0.95)
            ]
        }
        summary = get_detection_summary(results)

        assert summary['total_matches'] == 2
        assert summary['by_type']['phone_nl'] == 2
        assert summary['avg_confidence'] == 0.95
        assert summary['high_confidence'] == 2  # Both >= 0.9

    def test_get_detection_summary_multiple_types(self):
        """Test summary with multiple pattern types."""
        results = {
            'phone_nl': [('06-12345678', 0.95)],
            'email': [('test@example.com', 0.95)],
            'bsn': [('123456782', 1.0)]
        }
        summary = get_detection_summary(results)

        assert summary['total_matches'] == 3
        assert summary['by_type']['phone_nl'] == 1
        assert summary['by_type']['email'] == 1
        assert summary['by_type']['bsn'] == 1
        assert summary['avg_confidence'] > 0.9
        assert summary['high_confidence'] == 3

    def test_get_detection_summary_varying_confidence(self):
        """Test summary with varying confidence scores."""
        results = {
            'pattern1': [
                ('match1', 0.95),  # High confidence
                ('match2', 0.85),  # Medium confidence
                ('match3', 1.0)    # Perfect confidence
            ]
        }
        summary = get_detection_summary(results)

        assert summary['total_matches'] == 3
        assert summary['avg_confidence'] == 0.93  # (0.95 + 0.85 + 1.0) / 3
        assert summary['high_confidence'] == 2  # Only 0.95 and 1.0 are >= 0.9


class TestIntegration:
    """Integration tests for full validation pipeline."""

    def test_full_pipeline_with_context(self):
        """Test full 3-layer validation with context boosting."""
        validator = ThreeLayerValidator()

        text = """
        Persoonlijke gegevens:

        Burgerservicenummer: 123456782
        IBAN rekeningnummer: NL91ABNA0417164300
        Postcode adres: 1012JS
        Telefoon mobiel: 06-12345678
        Email contact: info@example.com
        """

        results = validator.detect_all(text)
        summary = get_detection_summary(results)

        # All patterns should be detected
        assert summary['total_matches'] >= 5

        # All should have high confidence (context words present)
        assert summary['high_confidence'] >= 5

        # Average confidence should be high
        assert summary['avg_confidence'] >= 0.9

    def test_false_positive_prevention(self):
        """Test that invalid patterns are not detected."""
        validator = ThreeLayerValidator()

        # Invalid BSN (bad checksum), invalid IBAN
        text = """
        Random numbers:
        123456789 (invalid BSN checksum)
        NL00FAKE0000000000 (invalid IBAN)
        """

        results = validator.detect_all(text)

        # Invalid BSN should not be detected
        if 'bsn' in results:
            assert len(results['bsn']) == 0

        # Invalid IBAN should not be detected
        if 'iban' in results:
            assert len(results['iban']) == 0
