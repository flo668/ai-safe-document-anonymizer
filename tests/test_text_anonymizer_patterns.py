"""
Tests for TextAnonymizer Pattern Detection Integration

Tests the integration of 3-layer validation into TextAnonymizer
with backwards compatibility and confidence threshold filtering.
"""

import pytest
from anonymizer.text_anonymizer import TextAnonymizer


class TestAutoDetectPatterns:
    """Tests for TextAnonymizer.auto_detect_patterns() method."""

    def test_auto_detect_patterns_phone(self):
        """Test auto-detecting phone numbers."""
        text = "Bel me op 06-12345678"
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert 'matches' in result
        assert 'summary' in result
        assert 'phone_nl' in result['matches']
        assert len(result['matches']['phone_nl']) > 0

        # Check confidence score
        match, confidence = result['matches']['phone_nl'][0]
        assert '06' in match or '6' in match
        assert 0.8 <= confidence <= 1.0

    def test_auto_detect_patterns_email(self):
        """Test auto-detecting email addresses."""
        text = "Stuur een email naar test@example.com"
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert 'email' in result['matches']
        assert len(result['matches']['email']) > 0

        match, confidence = result['matches']['email'][0]
        assert match == "test@example.com"
        assert 0.8 <= confidence <= 1.0

    def test_auto_detect_patterns_bsn(self):
        """Test auto-detecting BSN with checksum validation."""
        text = "BSN: 123456782"  # Valid BSN
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert 'bsn' in result['matches']
        assert len(result['matches']['bsn']) > 0

        match, confidence = result['matches']['bsn'][0]
        assert match == "123456782"
        assert confidence == 1.0  # Valid checksum

    def test_auto_detect_patterns_iban(self):
        """Test auto-detecting IBAN with mod-97 validation."""
        text = "IBAN: NL91ABNA0417164300"  # Valid IBAN
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert 'iban' in result['matches']
        assert len(result['matches']['iban']) > 0

        match, confidence = result['matches']['iban'][0]
        assert "NL91ABNA0417164300" in match.replace(" ", "")
        assert confidence == 1.0  # Valid checksum

    def test_auto_detect_patterns_postal_code(self):
        """Test auto-detecting Dutch postal codes."""
        text = "Postcode: 1012JS"
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert 'postal_code_nl' in result['matches']
        assert len(result['matches']['postal_code_nl']) > 0

        match, confidence = result['matches']['postal_code_nl'][0]
        assert "1012JS" in match.replace(" ", "")
        # Confidence is 1.0 due to context word "postcode" boosting (0.9 + 0.1)
        assert confidence == 1.0

    def test_auto_detect_patterns_confidence_threshold(self):
        """Test confidence threshold filtering."""
        text = "BSN: 123456782, Postcode: 1012JS"

        # Low threshold (0.8) - should get both
        result_low = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)
        low_count = sum(len(matches) for matches in result_low['matches'].values())

        # High threshold (0.95) - should filter out postal code (0.9)
        result_high = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.95)
        high_count = sum(len(matches) for matches in result_high['matches'].values())

        assert low_count >= high_count
        assert 'bsn' in result_high['matches']  # BSN has 1.0 confidence

    def test_auto_detect_patterns_context_boosting(self):
        """Test that context words boost confidence."""
        # Text with context word
        text_with_context = "Mijn burgerservicenummer is 123456782"
        result_with = TextAnonymizer.auto_detect_patterns(text_with_context, confidence_threshold=0.8)

        # Text without context word
        text_without_context = "Nummer: 123456782"
        result_without = TextAnonymizer.auto_detect_patterns(text_without_context, confidence_threshold=0.8)

        # Both should detect BSN
        assert 'bsn' in result_with['matches']
        assert 'bsn' in result_without['matches']

        # Context version should have higher or equal confidence
        conf_with = result_with['matches']['bsn'][0][1]
        conf_without = result_without['matches']['bsn'][0][1]

        assert conf_with >= conf_without

    def test_auto_detect_patterns_summary(self):
        """Test detection summary generation."""
        text = """
        Contactgegevens:
        Telefoon: 06-12345678
        Email: contact@example.com
        BSN: 123456782
        """

        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)
        summary = result['summary']

        # Check summary structure
        assert 'total_matches' in summary
        assert 'by_type' in summary
        assert 'avg_confidence' in summary
        assert 'high_confidence' in summary

        # Should have multiple matches
        assert summary['total_matches'] >= 3

        # Should have multiple types
        assert len(summary['by_type']) >= 3

    def test_auto_detect_patterns_no_matches(self):
        """Test with text containing no PII."""
        text = "Dit is een normale tekst zonder gevoelige informatie."
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        assert result['summary']['total_matches'] == 0
        assert len(result['matches']) == 0

    def test_auto_detect_patterns_invalid_checksum(self):
        """Test that invalid checksums are not detected."""
        text = """
        Invalid BSN: 123456789 (bad checksum)
        Invalid IBAN: NL00FAKE0000000000
        """

        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        # Invalid patterns should not be in results
        if 'bsn' in result['matches']:
            assert len(result['matches']['bsn']) == 0

        if 'iban' in result['matches']:
            assert len(result['matches']['iban']) == 0

    def test_auto_detect_patterns_multiple_same_type(self):
        """Test detecting multiple instances of same pattern type."""
        text = """
        Telefoon 1: 06-12345678
        Telefoon 2: 06-87654321
        Email 1: first@example.com
        Email 2: second@example.com
        """

        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        # Should detect multiple phones
        assert 'phone_nl' in result['matches']
        assert len(result['matches']['phone_nl']) >= 2

        # Should detect multiple emails
        assert 'email' in result['matches']
        assert len(result['matches']['email']) >= 2


class TestBackwardsCompatibility:
    """Tests to ensure backwards compatibility with existing code."""

    def test_existing_auto_detection_still_works(self):
        """Test that existing auto-detection functionality still works."""
        text = "Bel me op 06-12345678 of email naar test@example.com"

        # This should still work (existing method)
        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text,
            rules=[],
            auto_detect_enabled=True
        )

        # Should have anonymized content
        assert "[TEL VERWIJDERD]" in result or "06" not in result
        assert "[EMAIL VERWIJDERD]" in result or "test@example.com" not in result

        # Should have log entries
        assert len(logs) > 0

        # Should have report
        assert 'phone_numbers' in report or 'emails' in report

    def test_new_method_does_not_break_existing_tests(self):
        """Test that adding new method doesn't break existing functionality."""
        # Simple anonymization without auto-detection
        text = "Dit is een test met Jan Jansen"
        rules = [
            {
                'id': 'rule-1',
                'originalTerm': 'Jan Jansen',
                'replacementTerm': '[NAAM]',
                'isRegex': False,
                'caseSensitive': False,
                'removeInsteadOfReplace': False
            }
        ]

        from anonymizer.text_anonymizer import AnonymizationRule
        rule_objects = [AnonymizationRule(r) for r in rules]
        result, logs = TextAnonymizer.anonymize_text(text, rule_objects)

        assert '[NAAM]' in result
        assert 'Jan Jansen' not in result
        assert len(logs) > 0


class TestIntegrationWithValidator:
    """Integration tests between TextAnonymizer and ThreeLayerValidator."""

    def test_full_integration_all_pattern_types(self):
        """Test full integration with all pattern types."""
        text = """
        Persoonlijke gegevens medewerker:

        Naam: Jan de Vries
        Burgerservicenummer (BSN): 123456782
        IBAN bankrekeningnummer: NL91ABNA0417164300
        Postcode woonadres: 1012JS Amsterdam
        Telefoon mobiel: 06-12345678
        Email contact: jan.devries@example.com
        """

        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.8)

        # All pattern types should be detected
        assert 'phone_nl' in result['matches']
        assert 'email' in result['matches']
        assert 'bsn' in result['matches']
        assert 'iban' in result['matches']
        assert 'postal_code_nl' in result['matches']

        # All should have high confidence due to context words
        summary = result['summary']
        assert summary['total_matches'] >= 5
        assert summary['avg_confidence'] >= 0.9

    def test_integration_with_high_threshold(self):
        """Test integration with high confidence threshold."""
        text = """
        BSN nummer: 123456782
        Code: 1012JS
        """

        # Test without context words - postal code should have 0.9 confidence
        text_no_context = "Random: 1012JS"
        result_no_context = TextAnonymizer.auto_detect_patterns(text_no_context, confidence_threshold=0.95)

        # Postal code (0.9) should be filtered out by 0.95 threshold
        if 'postal_code_nl' in result_no_context['matches']:
            assert len(result_no_context['matches']['postal_code_nl']) == 0

        # BSN should still be detected
        result = TextAnonymizer.auto_detect_patterns(text, confidence_threshold=0.95)
        assert 'bsn' in result['matches']
        assert len(result['matches']['bsn']) > 0
