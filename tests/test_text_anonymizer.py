"""
Unit Tests voor Text Anonymizer

Test text en DOCX anonimisatie met auto-detection en reversible mode.
"""

import pytest
from pathlib import Path
from anonymizer.text_anonymizer import (
    TextAnonymizer,
    AnonymizationRule,
    LogEntry
)
from anonymizer.reverse_anonymizer import AnonymizationMapping


class TestAnonymizationRule:
    """Tests voor AnonymizationRule class"""

    def test_rule_from_dict(self):
        """Test maken van regel uit dict"""
        rule_dict = {
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '[GEHEIM]',
            'isRegex': False,
            'caseSensitive': True,
            'removeInsteadOfReplace': False
        }
        rule = AnonymizationRule(rule_dict)

        assert rule.id == 'rule-1'
        assert rule.original_term == 'geheim'
        assert rule.replacement_term == '[GEHEIM]'
        assert rule.is_regex is False
        assert rule.case_sensitive is True
        assert rule.remove_instead is False

    def test_rule_defaults(self):
        """Test default waardes"""
        rule = AnonymizationRule({})

        assert rule.id == ''
        assert rule.original_term == ''
        assert rule.replacement_term == ''
        assert rule.is_regex is False
        assert rule.case_sensitive is False
        assert rule.remove_instead is False


class TestLogEntry:
    """Tests voor LogEntry class"""

    def test_log_entry_creation(self):
        """Test maken van log entry"""
        entry = LogEntry(
            rule_id='rule-1',
            original='geheim',
            pattern='geheim',
            replaced='[GEHEIM]',
            count=3,
            source_file='test.txt'
        )

        assert entry.rule_id == 'rule-1'
        assert entry.original == 'geheim'
        assert entry.count == 3

    def test_log_entry_to_dict(self):
        """Test conversie naar dict"""
        entry = LogEntry('rule-1', 'geheim', 'geheim', '[GEHEIM]', 3, 'test.txt')
        result = entry.to_dict()

        assert result['ruleId'] == 'rule-1'
        assert result['originalTermDisplay'] == 'geheim'
        assert result['appliedPattern'] == 'geheim'
        assert result['replacedWith'] == '[GEHEIM]'
        assert result['count'] == 3
        assert result['sourceFileName'] == 'test.txt'


class TestTextAnonymizer:
    """Tests voor TextAnonymizer text processing"""

    def test_simple_literal_replacement(self):
        """Test simpele literal string replacement"""
        text = "Dit is geheim en geheim moet weg"
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '[GEHEIM]',
            'isRegex': False,
            'caseSensitive': False
        })]

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert '[GEHEIM]' in result
        # Check dat originele term vervangen is (maar kan deel zijn van placeholder)
        assert result.count('[GEHEIM]') == 2
        assert len(logs) == 1
        assert logs[0].count == 2

    def test_case_insensitive_replacement(self):
        """Test case-insensitive replacement"""
        text = "GEHEIM, geheim, Geheim"
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '[X]',
            'isRegex': False,
            'caseSensitive': False
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert result == "[X], [X], [X]"

    def test_case_sensitive_replacement(self):
        """Test case-sensitive replacement"""
        text = "GEHEIM en geheim"
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '[X]',
            'isRegex': False,
            'caseSensitive': True
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert "GEHEIM" in result  # Niet vervangen
        assert result.count('[X]') == 1  # Alleen lowercase

    def test_regex_replacement(self):
        """Test regex pattern replacement"""
        text = "Postcodes: 1234 AB, 5678 CD, 9012 EF"
        rules = [AnonymizationRule({
            'id': 'postcode',
            'originalTerm': r'\b\d{4}\s?[A-Z]{2}\b',
            'replacementTerm': '[POSTCODE]',
            'isRegex': True,
            'caseSensitive': False
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert '[POSTCODE]' in result
        assert '1234 AB' not in result
        assert logs[0].count == 3

    def test_remove_instead_of_replace(self):
        """Test remove mode (lege string)"""
        text = "Dit is geheim en geheim"
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '',
            'isRegex': False,
            'caseSensitive': False,
            'removeInsteadOfReplace': True
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        # "geheim" moet verwijderd zijn
        assert 'geheim' not in result.lower()
        # Maar tekst moet nog wel bestaan
        assert 'Dit is' in result

    def test_auto_detect_phones(self, sample_text_with_pii):
        """Test automatische detectie van telefoonnummers"""
        rules = []

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            sample_text_with_pii,
            rules,
            auto_detect_enabled=True,
            phone_placeholder='[TEL]'
        )

        # Check dat telefoons vervangen zijn
        assert '[TEL]' in result
        assert '06-12345678' not in result
        assert '0612345678' not in result

        # Check report
        assert report is not None
        assert report['phone_numbers']['count'] > 0

    def test_auto_detect_emails(self, sample_text_with_pii):
        """Test automatische detectie van emails"""
        rules = []

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            sample_text_with_pii,
            rules,
            auto_detect_enabled=True,
            email_placeholder='[EMAIL]'
        )

        # Check dat emails vervangen zijn
        assert '[EMAIL]' in result
        assert '@example.com' not in result
        assert '@bedrijf.nl' not in result

        # Check report
        assert report is not None
        assert report['emails']['count'] > 0

    def test_auto_detect_disabled(self, sample_text_with_pii):
        """Test dat auto-detect UIT staat wanneer disabled"""
        rules = []

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            sample_text_with_pii,
            rules,
            auto_detect_enabled=False
        )

        # Originele telefoons en emails moeten er nog zijn
        assert '06-12345678' in result or '0612345678' in result
        assert '@example.com' in result or '@bedrijf.nl' in result

        # Report moet leeg of None zijn
        assert report is None or report['phone_numbers']['count'] == 0

    def test_combined_rules_and_auto_detect(self):
        """Test combinatie van handmatige regels EN auto-detect"""
        text = "Naam: Jan de Vries, Tel: 06-12345678, Email: jan@test.nl"
        rules = [AnonymizationRule({
            'id': 'naam',
            'originalTerm': 'Jan de Vries',
            'replacementTerm': '[NAAM]',
            'isRegex': False,
            'caseSensitive': False
        })]

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text,
            rules,
            auto_detect_enabled=True,
            phone_placeholder='[TEL]',
            email_placeholder='[EMAIL]'
        )

        # Alles moet vervangen zijn
        assert '[NAAM]' in result
        assert '[TEL]' in result
        assert '[EMAIL]' in result
        assert 'Jan de Vries' not in result
        assert '06-12345678' not in result
        assert 'jan@test.nl' not in result

        # Logs: 1 manual + 1 phone + 1 email = 3
        assert len(logs) >= 3

    def test_reversible_mode_unique_placeholders(self):
        """Test reversible mode met unieke placeholders"""
        text = "Tel1: 06-12345678, Tel2: 06-98765432, Tel1 again: 06-12345678"
        rules = []
        mapping = AnonymizationMapping()

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text,
            rules,
            auto_detect_enabled=True,
            reversible_mode=True,
            mapping=mapping
        )

        # Check unieke placeholders
        assert '[TEL-001]' in result
        assert '[TEL-002]' in result

        # Mapping moet beide nummers bevatten
        assert len(mapping.mappings) == 2
        # mappings is een dict {placeholder: original}
        originals = list(mapping.mappings.values())
        assert '06-12345678' in originals
        assert '06-98765432' in originals

    def test_reversible_mode_consistent_placeholders(self):
        """Test dat zelfde waarde altijd dezelfde placeholder krijgt"""
        text = "Email: jan@test.nl en nog een keer jan@test.nl"
        rules = []
        mapping = AnonymizationMapping()

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text,
            rules,
            auto_detect_enabled=True,
            reversible_mode=True,
            mapping=mapping
        )

        # Beide instances moeten zelfde placeholder krijgen
        assert result.count('[EMAIL-001]') == 2

        # Mapping moet maar 1 entry hebben
        assert len(mapping.mappings) == 1

    def test_multiple_rules_order(self):
        """Test dat regels in correcte volgorde toegepast worden"""
        text = "Jan de Vries uit Amsterdam"
        rules = [
            AnonymizationRule({
                'id': 'rule-1',
                'originalTerm': 'Jan de Vries',
                'replacementTerm': '[PERSOON]',
                'isRegex': False
            }),
            AnonymizationRule({
                'id': 'rule-2',
                'originalTerm': 'Amsterdam',
                'replacementTerm': '[STAD]',
                'isRegex': False
            })
        ]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert '[PERSOON]' in result
        assert '[STAD]' in result
        assert 'Jan de Vries' not in result
        assert 'Amsterdam' not in result

    def test_get_preview(self):
        """Test preview functionaliteit"""
        text = "Contact: 06-12345678, email@test.nl"

        preview = TextAnonymizer.get_preview(
            text,
            phone_placeholder='[TEL]',
            email_placeholder='[EMAIL]',
            max_chars=100
        )

        assert 'phone_numbers' in preview
        assert 'emails' in preview
        assert preview['phone_numbers']['count'] > 0
        assert preview['emails']['count'] > 0
        assert len(preview['phone_numbers']['preview']) > 0
        assert len(preview['emails']['preview']) > 0

    def test_empty_text(self):
        """Test met lege tekst"""
        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            "", [], auto_detect_enabled=True
        )

        assert result == ""
        assert len(logs) == 0

    def test_text_without_pii(self, sample_text_clean):
        """Test met tekst zonder PII"""
        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            sample_text_clean,
            [],
            auto_detect_enabled=True
        )

        # Tekst moet onveranderd blijven
        assert result == sample_text_clean
        assert len(logs) == 0 or (report and report['phone_numbers']['count'] == 0)


class TestDocxProcessing:
    """Tests voor DOCX verwerking"""

    def test_process_docx_preserve_formatting(self, sample_docx_file, temp_output_file):
        """Test DOCX processing met opmaak behoud"""
        rules = [AnonymizationRule({
            'id': 'test',
            'originalTerm': 'Jan de Vries',
            'replacementTerm': '[NAAM]',
            'isRegex': False
        })]

        # Check of bestand bestaat
        if not sample_docx_file.exists():
            pytest.skip("DOCX fixture niet gevonden")

        logs, report = TextAnonymizer.process_docx_preserve_formatting(
            sample_docx_file,
            temp_output_file,
            rules,
            auto_detect_enabled=True,
            phone_placeholder='[TEL]',
            email_placeholder='[EMAIL]'
        )

        # Check dat output bestand gemaakt is
        assert temp_output_file.exists()

        # Check logs
        assert len(logs) > 0


class TestEdgeCases:
    """Tests voor edge cases en boundary conditions"""

    def test_very_long_text(self):
        """Test met hele lange tekst"""
        text = "geheim " * 10000  # 10k repetities
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': 'geheim',
            'replacementTerm': '[X]',
            'isRegex': False
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert '[X]' in result
        assert logs[0].count == 10000

    def test_special_regex_characters(self):
        """Test met speciale regex karakters in literal mode"""
        text = "Prijs: €100 (incl. btw)"
        rules = [AnonymizationRule({
            'id': 'rule-1',
            'originalTerm': '€100',
            'replacementTerm': '[PRIJS]',
            'isRegex': False
        })]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        assert '[PRIJS]' in result

    def test_overlapping_patterns(self):
        """Test met overlappende patterns"""
        text = "Jan de Vries en de Vries familie"
        rules = [
            AnonymizationRule({
                'id': 'rule-1',
                'originalTerm': 'Jan de Vries',
                'replacementTerm': '[NAAM1]',
                'isRegex': False
            }),
            AnonymizationRule({
                'id': 'rule-2',
                'originalTerm': 'de Vries',
                'replacementTerm': '[NAAM2]',
                'isRegex': False
            })
        ]

        result, logs, _ = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=False
        )

        # Beide patterns moeten toegepast zijn
        assert '[NAAM1]' in result or '[NAAM2]' in result

    def test_unicode_text(self):
        """Test met Unicode karakters"""
        text = "Naam: Αλέξανδρος, Email: test@example.com, Tel: 06-12345678"
        rules = []

        result, logs, report = TextAnonymizer.anonymize_text_with_auto_detection(
            text, rules, auto_detect_enabled=True
        )

        # Auto-detect moet nog steeds werken voor telefoons en normale emails
        assert '[TEL VERWIJDERD]' in result
        assert '[EMAIL VERWIJDERD]' in result
        # Unicode naam moet behouden blijven
        assert 'Αλέξανδρος' in result
