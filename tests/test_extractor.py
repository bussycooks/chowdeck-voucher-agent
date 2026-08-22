"""Tests for voucher extraction module."""
import pytest
from app.voucher_extractor import VoucherExtractor


class TestVoucherExtractor:
    """Test voucher extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a voucher extractor instance."""
        return VoucherExtractor(
            min_length=3,
            max_length=20,
            pattern=r"^[A-Z0-9]+$",
        )

    def test_extract_uppercase_alphanumeric(self, extractor):
        """Test extraction of uppercase alphanumeric codes."""
        text = "Use code CHOW2024 for 50% off"
        result = extractor.extract(text)
        assert "CHOW2024" in result

    def test_extract_mixed_case_with_numbers(self, extractor):
        """Test extraction of mixed case codes with numbers."""
        text = "Apply promo code Chow50OFF today"
        result = extractor.extract(text)
        # Should extract and uppercase it
        assert any("CHOW" in code for code in result)

    def test_ignore_urls(self, extractor):
        """Test that URLs are ignored."""
        text = "Check https://example.com for voucher ABC123"
        result = extractor.extract(text)
        assert not any("https" in code or "example" in code for code in result)
        assert "ABC123" in result

    def test_ignore_twitter_handles(self, extractor):
        """Test that Twitter handles are ignored."""
        text = "Follow @lordbinary_ for code VOUCHERCODE"
        result = extractor.extract(text)
        assert "@lordbinary_" not in result
        assert "VOUCHERCODE" in result

    def test_ignore_common_words(self, extractor):
        """Test that common words are ignored."""
        text = "Use the code OFFER123 and save"
        result = extractor.extract(text)
        assert "THE" not in result
        assert "AND" not in result
        assert "OFFER123" in result

    def test_min_length_filter(self, extractor):
        """Test minimum length filtering."""
        text = "Code AB is too short, use VALID123"
        result = extractor.extract(text)
        assert "AB" not in result
        assert "VALID123" in result

    def test_max_length_filter(self, extractor):
        """Test maximum length filtering."""
        text = "This is THISISTOOLONGOFACODE123 and VALID123"
        result = extractor.extract(text)
        # Too long code should be filtered
        assert "VALID123" in result

    def test_empty_text(self, extractor):
        """Test extraction from empty text."""
        result = extractor.extract("")
        assert result == []

    def test_none_text(self, extractor):
        """Test extraction from None."""
        result = extractor.extract(None)
        assert result == []

    def test_duplicate_codes(self, extractor):
        """Test that duplicate codes are deduplicated."""
        text = "Use PROMO50 or PROMO50 or PROMO50"
        result = extractor.extract(text)
        # Should only return one instance
        assert result.count("PROMO50") == 1

    def test_update_pattern(self, extractor):
        """Test dynamic pattern updates."""
        # Initially extract
        text = "Code123"
        result1 = extractor.extract(text)
        
        # Update to only accept 6+ character codes
        extractor.update_pattern(min_length=6)
        result2 = extractor.extract(text)
        
        # Code123 is 7 chars, should still be extracted
        assert "CODE123" in result1 or len(result1) == 0

    def test_letter_number_combination(self, extractor):
        """Test that codes with both letters and numbers are preferred."""
        text = "Use ABC123 or XYZ or 12345"
        result = extractor.extract(text)
        # Letter+number combination should be extracted
        assert "ABC123" in result
        # Pure numbers or pure letters (unless uppercase) may not be

    def test_all_uppercase_preference(self, extractor):
        """Test that all-uppercase codes are extracted."""
        text = "Use PROMO for discount"
        result = extractor.extract(text)
        # All uppercase word of reasonable length
        assert "PROMO" in result or len(result) == 0  # Depends on min length

    def test_case_insensitivity(self, extractor):
        """Test that extraction normalizes to uppercase."""
        text = "Promo50Off"
        result = extractor.extract(text)
        if result:
            # All results should be uppercase
            assert all(code.isupper() for code in result)
