"""
Unit Tests voor Pattern Matching

Test alle regex patterns voor telefoons en emails.
"""

import pytest
from anonymizer.patterns import PhoneNumberPatterns, EmailPatterns, BSNPatterns, IBANPatterns, PostalCodePatterns, detect_bsn, detect_iban, detect_postal_codes
from utils.validators import validate_bsn, validate_iban, validate_postal_code_nl


class TestPhoneNumberPatterns:
    """Tests voor Nederlandse telefoonnummer patterns"""

    def test_mobile_dash(self):
        """Test 06-12345678 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_DASH
        assert pattern.search("06-12345678")
        assert pattern.search("Bel: 06-12345678 voor info")
        assert pattern.search("06 -12345678")  # Met spatie
        assert not pattern.search("0612345678")  # Zonder streepje

    def test_mobile_spaces(self):
        """Test 06 12 34 56 78 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_SPACES
        assert pattern.search("06 12 34 56 78")
        assert pattern.search("06-12-34-56-78")
        assert pattern.search("06.12.34.56.78")

    def test_mobile_universal(self):
        """Test universeel pattern met verschillende scheiders"""
        pattern = PhoneNumberPatterns.MOBILE_UNIVERSAL
        assert pattern.search("06 12 34 56 78")
        assert pattern.search("06-12-34-56-78")
        assert pattern.search("0612345678")
        assert pattern.search("06  12  34  56  78")  # Extra spaties

    def test_mobile_intl_plus(self):
        """Test +31612345678 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_INTL_PLUS
        assert pattern.search("+31612345678")
        assert pattern.search("+31 612345678")
        assert pattern.search("+31-612345678")
        assert pattern.search("+31 6 12345678")

    def test_mobile_intl_plus_spaces(self):
        """Test +31 6 12 34 56 78 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_INTL_PLUS_SPACES
        assert pattern.search("+31 6 12 34 56 78")
        assert pattern.search("+31-6-12-34-56-78")
        assert pattern.search("+316 12 34 56 78")

    def test_mobile_intl_zero(self):
        """Test 0031612345678 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_INTL_ZERO
        assert pattern.search("0031612345678")
        assert pattern.search("0031 612345678")
        assert pattern.search("0031 6 12345678")

    def test_mobile_intl_zero_spaces(self):
        """Test 0031 6 12 34 56 78 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_INTL_ZERO_SPACES
        assert pattern.search("0031 6 12 34 56 78")
        assert pattern.search("00316 12 34 56 78")
        assert pattern.search("0031 6.12.34.56.78")

    def test_mobile_parentheses(self):
        """Test (06) 12345678 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_PARENTHESES
        assert pattern.search("(06) 12345678")
        assert pattern.search("(06)12345678")
        assert pattern.search("( 06 ) 12345678")

    def test_mobile_dots(self):
        """Test 06.12.34.56.78 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_DOTS
        assert pattern.search("06.12.34.56.78")
        assert pattern.search("Contact: 06.12.34.56.78")

    def test_mobile_simple(self):
        """Test simpel 0612345678 formaat"""
        pattern = PhoneNumberPatterns.MOBILE_SIMPLE
        assert pattern.search("0612345678")
        assert pattern.search("06 12345678")
        assert pattern.search("Mobiel: 0612345678")

    def test_mobile_single_space(self):
        """Test 06 12345678 formaat (veel voorkomend)"""
        pattern = PhoneNumberPatterns.MOBILE_SINGLE_SPACE
        assert pattern.search("06 12345678")
        assert pattern.search("Bel 06 28659589 voor meer info")

    def test_landline_dash(self):
        """Test vast nummer 010-1234567 formaat"""
        pattern = PhoneNumberPatterns.LANDLINE_DASH
        assert pattern.search("010-1234567")
        assert pattern.search("020-1234567")
        assert pattern.search("030 1234567")
        assert pattern.search("0800-123456")  # Gratis nummer

    def test_landline_intl(self):
        """Test internationaal vast nummer +31 10 1234567"""
        pattern = PhoneNumberPatterns.LANDLINE_INTL
        assert pattern.search("+31 10 1234567")
        assert pattern.search("+31-20-1234567")
        assert pattern.search("+31 20 1234567")

    def test_get_all_patterns(self):
        """Test dat alle patterns beschikbaar zijn"""
        patterns = PhoneNumberPatterns.get_all_patterns()
        assert len(patterns) == 13
        assert all(hasattr(p, 'search') for p in patterns)

    @pytest.mark.parametrize("phone", [
        "06-12345678",
        "0612345678",
        "+31612345678",
        "06 12345678",
        "06 12 34 56 78",
        "+31 6 12345678",
        "0031612345678",
        "(06) 12345678",
        "06.12.34.56.78"
    ])
    def test_all_formats_matched(self, phone):
        """Test dat alle voorkomende formaten gematcht worden door minimaal 1 pattern"""
        patterns = PhoneNumberPatterns.get_all_patterns()
        matched = any(p.search(phone) for p in patterns)
        assert matched, f"Telefoon {phone} wordt niet gematcht door enig pattern"


class TestEmailPatterns:
    """Tests voor email patterns"""

    def test_standard_pattern(self):
        """Test standaard email pattern"""
        pattern = EmailPatterns.STANDARD
        assert pattern.search("test@example.com")
        assert pattern.search("jan.de.vries@bedrijf.nl")
        assert pattern.search("info@sub.domain.com")
        assert pattern.search("user+tag@gmail.com")
        assert pattern.search("admin@localhost.local")

    def test_permissive_pattern(self):
        """Test permissive email pattern voor edge cases"""
        pattern = EmailPatterns.PERMISSIVE
        assert pattern.search("a@b.co")
        assert pattern.search("user123@test.org")
        assert pattern.search("info@domain.co.uk")

    def test_email_in_text(self):
        """Test email detectie in normale tekst"""
        pattern = EmailPatterns.STANDARD
        text = "Neem contact op via info@bedrijf.nl voor meer informatie"
        match = pattern.search(text)
        assert match
        assert match.group() == "info@bedrijf.nl"

    def test_multiple_emails(self):
        """Test detectie van meerdere emails"""
        pattern = EmailPatterns.STANDARD
        text = "Contact: jan@test.nl, maria@bedrijf.nl, support@example.com"
        matches = pattern.findall(text)
        assert len(matches) == 3
        assert "jan@test.nl" in matches
        assert "maria@bedrijf.nl" in matches
        assert "support@example.com" in matches

    def test_get_all_patterns(self):
        """Test dat email patterns beschikbaar zijn"""
        patterns = EmailPatterns.get_all_patterns()
        assert len(patterns) == 2
        assert EmailPatterns.STANDARD in patterns
        assert EmailPatterns.PERMISSIVE in patterns

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "jan.de.vries@bedrijf.nl",
        "info@sub.domain.com",
        "user+tag@gmail.com",
        "admin@localhost.org",
        "a@b.co",
        "user_123@test-domain.nl"
    ])
    def test_valid_emails(self, email):
        """Test dat valide emails worden gematcht"""
        patterns = EmailPatterns.get_all_patterns()
        matched = any(p.search(email) for p in patterns)
        assert matched, f"Email {email} wordt niet gematcht"

    @pytest.mark.parametrize("invalid", [
        "@example.com",
        "user@",
        "user",
        "user@.com",
        "user@domain"
    ])
    def test_invalid_emails(self, invalid):
        """Test dat ongeldige emails NIET worden gematcht"""
        pattern = EmailPatterns.STANDARD
        assert not pattern.search(invalid), f"Ongeldig email {invalid} wordt toch gematcht"


class TestBSNPatterns:
    """Tests voor BSN (Burgerservicenummer) patterns"""

    def test_bsn_plain(self):
        """Test 9-digit BSN formaat"""
        pattern = BSNPatterns.PLAIN
        assert pattern.search("123456782")
        assert pattern.search("BSN: 123456782 is geldig")
        assert not pattern.search("12345678")  # Te kort
        assert not pattern.search("1234567890")  # Te lang

    def test_bsn_dashes(self):
        """Test BSN met streepjes (123-45-6782)"""
        pattern = BSNPatterns.DASHES
        assert pattern.search("123-45-6782")
        assert pattern.search("BSN: 123-45-6782")

    def test_bsn_dots(self):
        """Test BSN met punten (123.45.6782)"""
        pattern = BSNPatterns.DOTS
        assert pattern.search("123.45.6782")
        assert pattern.search("Nummer: 123.45.6782")

    def test_get_all_patterns(self):
        """Test dat alle BSN patterns beschikbaar zijn"""
        patterns = BSNPatterns.get_all_patterns()
        assert len(patterns) == 3
        assert all(hasattr(p, 'search') for p in patterns)

    def test_validate_bsn_valid(self):
        """Test 11-proef validatie met geldige BSNs"""
        # Valid BSN met correcte checksum
        assert validate_bsn("123456782") == True
        # BSN met formatting
        assert validate_bsn("123-45-6782") == True
        assert validate_bsn("123.45.6782") == True

    def test_validate_bsn_invalid_checksum(self):
        """Test dat ongeldige checksums worden afgewezen"""
        assert validate_bsn("123456783") == False  # Checksum fout
        assert validate_bsn("123456781") == False  # Checksum fout

    def test_validate_bsn_deny_list(self):
        """Test dat test BSNs worden afgewezen"""
        assert validate_bsn("000000000") == False
        assert validate_bsn("111111111") == False
        assert validate_bsn("999999999") == False

    def test_validate_bsn_invalid_format(self):
        """Test dat ongeldige formaten worden afgewezen"""
        assert validate_bsn("12345678") == False  # Te kort
        assert validate_bsn("1234567890") == False  # Te lang
        assert validate_bsn("abcdefghi") == False  # Geen cijfers

    def test_detect_bsn(self):
        """Test BSN detection met checksum validatie"""
        text = """
        Valid BSN: 123456782
        Invalid BSN: 123456783
        Test BSN: 000000000
        Random number: 987654321
        """
        results = detect_bsn(text)

        # Should only detect valid BSN
        assert len(results) == 1
        assert results[0][0] == "123456782"
        assert results[0][1] == 1.0  # High confidence

    def test_detect_bsn_no_false_positives(self):
        """Test dat random 9-digit numbers niet als BSN worden gedetecteerd"""
        text = """
        Order ID: 123456789
        Transaction: 987654321
        Date: 20240115
        """
        results = detect_bsn(text)

        # Should detect nothing (geen geldige checksums)
        assert len(results) == 0


class TestIBANPatterns:
    """Tests voor IBAN patterns"""

    def test_iban_nl(self):
        """Test Nederlandse IBAN (18 chars)"""
        pattern = IBANPatterns.NL
        assert pattern.search("NL91ABNA0417164300")
        assert pattern.search("NL91 ABNA 0417 1643 00")
        assert pattern.search("IBAN: NL91ABNA0417164300")

    def test_iban_de(self):
        """Test Duitse IBAN (22 chars)"""
        pattern = IBANPatterns.DE
        assert pattern.search("DE89370400440532013000")
        assert pattern.search("DE89 3704 0044 0532 0130 00")

    def test_iban_be(self):
        """Test Belgische IBAN (16 chars)"""
        pattern = IBANPatterns.BE
        assert pattern.search("BE68539007547034")
        assert pattern.search("BE68 5390 0754 7034")

    def test_iban_fr(self):
        """Test Franse IBAN (27 chars)"""
        pattern = IBANPatterns.FR
        assert pattern.search("FR1420041010050500013M02606")
        assert pattern.search("FR14 2004 1010 0505 0001 3M02 606")

    def test_get_all_patterns(self):
        """Test dat alle IBAN patterns beschikbaar zijn"""
        patterns = IBANPatterns.get_all_patterns()
        assert len(patterns) == 4
        assert all(hasattr(p, 'search') for p in patterns)

    def test_validate_iban_valid_nl(self):
        """Test mod-97 validatie met geldige Nederlandse IBANs"""
        assert validate_iban("NL91ABNA0417164300") == True
        assert validate_iban("NL91 ABNA 0417 1643 00") == True  # Met spaties

    def test_validate_iban_invalid_checksum(self):
        """Test dat ongeldige checksums worden afgewezen"""
        assert validate_iban("NL00FAKE0000000000") == False
        assert validate_iban("NL99TEST0000000000") == False

    def test_validate_iban_invalid_length(self):
        """Test dat ongeldige lengtes worden afgewezen"""
        assert validate_iban("NL91ABNA041716") == False  # Te kort
        assert validate_iban("NL91ABNA04171643001234") == False  # Te lang

    def test_validate_iban_unknown_country(self):
        """Test dat onbekende landcodes worden afgewezen"""
        assert validate_iban("XX91ABNA0417164300") == False
        assert validate_iban("ZZ123456789012345678") == False

    def test_detect_iban(self):
        """Test IBAN detection met mod-97 validatie"""
        text = """
        Valid IBAN: NL91ABNA0417164300
        Invalid IBAN: NL00FAKE0000000000
        Random: AB12CD34EF56GH78IJ
        """
        results = detect_iban(text)

        # Should only detect valid IBAN
        assert len(results) == 1
        assert results[0][0] == "NL91ABNA0417164300"
        assert results[0][1] == 1.0  # High confidence

    def test_detect_iban_multiple_countries(self):
        """Test IBAN detection voor meerdere landen"""
        text = """
        NL: NL91ABNA0417164300
        DE: DE89370400440532013000
        BE: BE68539007547034
        """
        results = detect_iban(text)

        # Should detect all valid IBANs
        assert len(results) == 3


class TestPostalCodePatterns:
    """Tests voor Dutch postal code patterns"""

    def test_postal_code_standard(self):
        """Test standard postal code formaat (1234AB)"""
        pattern = PostalCodePatterns.STANDARD
        assert pattern.search("1012JS")
        assert pattern.search("1234AB")
        assert pattern.search("Adres: 1012JS Amsterdam")
        assert pattern.search("1012 JS")  # Met spatie

    def test_get_all_patterns(self):
        """Test dat alle postal code patterns beschikbaar zijn"""
        patterns = PostalCodePatterns.get_all_patterns()
        assert len(patterns) == 1
        assert all(hasattr(p, 'search') for p in patterns)

    def test_validate_postal_code_valid(self):
        """Test validatie met geldige postal codes"""
        assert validate_postal_code_nl("1012JS") == True
        assert validate_postal_code_nl("1234AB") == True
        assert validate_postal_code_nl("1012 JS") == True  # Met spatie
        assert validate_postal_code_nl("9711LM") == True

    def test_validate_postal_code_invalid_reserved(self):
        """Test dat reserved letter combinations worden afgewezen"""
        assert validate_postal_code_nl("1234SA") == False  # PO box reserved
        assert validate_postal_code_nl("1234SD") == False  # PO box reserved
        assert validate_postal_code_nl("1234SS") == False  # PO box reserved

    def test_validate_postal_code_invalid_format(self):
        """Test dat ongeldige formaten worden afgewezen"""
        assert validate_postal_code_nl("12345") == False  # Te kort
        assert validate_postal_code_nl("123AB") == False  # Verkeerde lengte
        assert validate_postal_code_nl("ABCD12") == False  # Letters eerst

    def test_detect_postal_codes(self):
        """Test postal code detection met validatie"""
        text = """
        Amsterdam: 1012JS
        Rotterdam: 3011AD
        Reserved: 1234SA
        """
        results = detect_postal_codes(text)

        # Should detect valid codes, not reserved ones
        assert len(results) == 2
        assert results[0][1] == 0.9  # Medium-high confidence
        assert results[1][1] == 0.9

    def test_detect_postal_codes_in_address(self):
        """Test postal code detection in volledig adres"""
        text = "Kalverstraat 123, 1012JS Amsterdam"
        results = detect_postal_codes(text)

        assert len(results) == 1
        assert results[0][0].replace(" ", "").upper() == "1012JS"


class TestPatternIntegration:
    """Integration tests voor pattern matching"""

    def test_mixed_content(self):
        """Test detectie in gemixte tekst met zowel telefoons als emails"""
        text = """
        Contactpersoon: Jan de Vries
        Telefoon: 06-12345678
        Email: jan.devries@example.com

        Kantoor: 020-1234567
        Info: info@bedrijf.nl
        """

        phone_patterns = PhoneNumberPatterns.get_all_patterns()
        email_patterns = EmailPatterns.get_all_patterns()

        # Check telefoonnummers
        phones_found = []
        for pattern in phone_patterns:
            phones_found.extend(pattern.findall(text))
        assert len(phones_found) >= 2  # Minimaal mobiel en vast nummer

        # Check emails
        emails_found = []
        for pattern in email_patterns:
            emails_found.extend(pattern.findall(text))
        assert len(set(emails_found)) >= 2  # Minimaal 2 unieke emails

    def test_no_false_positives(self):
        """Test dat patterns geen false positives geven in normale tekst"""
        text = "Dit is een test met 123456789 en test.com en @mention"

        phone_patterns = PhoneNumberPatterns.get_all_patterns()
        email_patterns = EmailPatterns.get_all_patterns()

        # Geen telefoons
        phones_found = []
        for pattern in phone_patterns:
            phones_found.extend(pattern.findall(text))
        assert len(phones_found) == 0, "False positive voor telefoonnummer"

        # Geen emails
        emails_found = []
        for pattern in email_patterns:
            emails_found.extend(pattern.findall(text))
        assert len(emails_found) == 0, "False positive voor email"
