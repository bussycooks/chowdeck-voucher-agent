"""Voucher extraction module.

Identifies likely Chowdeck voucher codes from tweet text.
Designed to be easily updated as voucher format patterns emerge.
"""
import re
import logging
from typing import List, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VoucherPattern:
    """Represents a voucher code pattern."""
    pattern: str
    min_length: int = 3
    max_length: int = 20
    description: str = "Generic alphanumeric code"


class VoucherExtractor:
    """Extracts potential voucher codes from text."""
    
    # Common patterns that are definitely NOT vouchers
    EXCLUSION_PATTERNS = [
        r"^http",  # URLs
        r"^www\.",  # Website references
        r"^@",  # Twitter handles
        r"#",  # Hashtags
        r"^the$",  # Common words
        r"^a$",
        r"^and$",
        r"^or$",
        r"^is$",
        r"^to$",
        r"^for$",
        r"^in$",
        r"^use$",
        r"^on$",
        r"^at$",
    ]
    
    def __init__(
        self,
        min_length: int = 3,
        max_length: int = 20,
        pattern: str = r"^[A-Z0-9]+$",
    ):
        """Initialize the voucher extractor.
        
        Args:
            min_length: Minimum voucher code length
            max_length: Maximum voucher code length
            pattern: Regex pattern for valid voucher codes
        """
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern)
        self.exclusion_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXCLUSION_PATTERNS]
        
    def extract(self, text: str) -> List[str]:
        """Extract potential voucher codes from text.
        
        Args:
            text: Tweet or text content to scan
            
        Returns:
            List of potential voucher codes (deduplicated)
        """
        if not text or not isinstance(text, str):
            return []
        
        # Remove URLs from text
        cleaned_text = self._remove_urls(text)
        
        # Split into words and filter
        candidates = self._extract_candidates(cleaned_text)
        
        # Filter with validation
        vouchers = self._validate_candidates(candidates)
        
        # Return unique codes
        return list(set(vouchers))
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        url_pattern = r"https?://\S+|www\.\S+"
        return re.sub(url_pattern, "", text)
    
    def _extract_candidates(self, text: str) -> List[str]:
        """Extract candidate words that might be voucher codes."""
        # Match words that are mostly uppercase or alphanumeric
        # This includes camelCase and lowercase
        candidates = []
        
        # Look for sequences of letters and numbers
        # Avoid extracting from normal sentences
        words = text.split()
        
        for word in words:
            # Remove punctuation from the word
            clean_word = re.sub(r"[^a-zA-Z0-9]", "", word)
            
            # Skip if empty after cleaning
            if not clean_word:
                continue
            
            # Check length
            if not (self.min_length <= len(clean_word) <= self.max_length):
                continue
            
            # Skip if it's just numbers or just letters (too common)
            if clean_word.isdigit() or clean_word.isalpha():
                # Only include all-alpha if it's uppercase (more likely to be a code)
                if clean_word.isalpha() and not clean_word.isupper():
                    continue
            
            # If it contains both letters and numbers, it's a good candidate
            has_letter = any(c.isalpha() for c in clean_word)
            has_number = any(c.isdigit() for c in clean_word)
            
            if has_letter and has_number:
                candidates.append(clean_word.upper())
            elif clean_word.isupper() and len(clean_word) >= self.min_length:
                # All-uppercase words of reasonable length are candidates
                candidates.append(clean_word)
        
        return candidates
    
    def _validate_candidates(self, candidates: List[str]) -> List[str]:
        """Validate and filter candidate codes."""
        valid_codes = []
        
        for candidate in candidates:
            # Check against exclusion patterns
            if self._is_excluded(candidate):
                logger.debug(f"Excluding candidate: {candidate} (matched exclusion pattern)")
                continue
            
            # Check against main pattern
            if not self.pattern.match(candidate):
                logger.debug(f"Excluding candidate: {candidate} (doesn't match pattern)")
                continue
            
            valid_codes.append(candidate)
        
        return valid_codes
    
    def _is_excluded(self, text: str) -> bool:
        """Check if text matches any exclusion pattern."""
        return any(pattern.search(text) for pattern in self.exclusion_patterns)
    
    def update_pattern(
        self,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ):
        """Update extraction patterns dynamically.
        
        This allows fine-tuning based on observed voucher formats.
        """
        if pattern:
            self.pattern = re.compile(pattern)
            logger.info(f"Updated voucher pattern to: {pattern}")
        
        if min_length is not None:
            self.min_length = min_length
            logger.info(f"Updated min_length to: {min_length}")
        
        if max_length is not None:
            self.max_length = max_length
            logger.info(f"Updated max_length to: {max_length}")
