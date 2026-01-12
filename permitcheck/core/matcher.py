"""License matching and normalization for PermitCheck."""

import re
from typing import Set, Dict, Optional, List
from difflib import SequenceMatcher


class SPDXExpressionParser:
    """Parser for SPDX license expressions."""
    
    # SPDX operators (case-insensitive)
    OPERATORS = ['OR', 'AND', 'WITH']
    
    @staticmethod
    def parse(expression: str) -> List[str]:
        """Parse SPDX expression into individual license identifiers.
        
        Handles expressions like:
        - "MIT OR Apache-2.0"
        - "GPL-2.0+ WITH Classpath-exception"
        - "(MIT OR Apache-2.0) AND BSD-3-Clause"
        
        Args:
            expression: SPDX license expression
            
        Returns:
            List of individual license identifiers
        """
        if not expression:
            return []
        
        # Remove parentheses
        expression = expression.replace('(', ' ').replace(')', ' ')
        
        # Split by operators (case-insensitive)
        tokens = [expression]
        for op in SPDXExpressionParser.OPERATORS:
            new_tokens = []
            for token in tokens:
                # Split on operator with word boundaries
                parts = re.split(fr'\s+{op}\s+', token, flags=re.IGNORECASE)
                new_tokens.extend(parts)
            tokens = new_tokens
        
        # Clean and filter tokens
        licenses = []
        for token in tokens:
            token = token.strip()
            if token and token.upper() not in SPDXExpressionParser.OPERATORS:
                # Handle + suffix (GPL-2.0+ means GPL-2.0-or-later)
                if token.endswith('+'):
                    base = token[:-1].strip()
                    licenses.append(f"{base}-or-later")
                else:
                    licenses.append(token)
        
        return licenses


class LicenseMatcher:
    """Matches and normalizes license identifiers."""
    
    # Common license variations and their normalized forms
    NORMALIZATIONS = {
        'apache': 'Apache',
        'apache 2.0': 'Apache-2.0',
        'apache 2': 'Apache-2.0',
        'apache license 2.0': 'Apache-2.0',
        'apache license': 'Apache-2.0',
        'mit license': 'MIT',
        'mit': 'MIT',
        'bsd': 'BSD',
        'bsd license': 'BSD',
        'bsd 3-clause': 'BSD-3-Clause',
        'bsd 2-clause': 'BSD-2-Clause',
        '3-clause bsd': 'BSD-3-Clause',
        '2-clause bsd': 'BSD-2-Clause',
        'gpl': 'GPL',
        'gplv2': 'GPL-2.0',
        'gplv3': 'GPL-3.0',
        'gpl v2': 'GPL-2.0',
        'gpl v3': 'GPL-3.0',
        'lgpl': 'LGPL',
        'lgplv2': 'LGPL-2.0',
        'lgplv3': 'LGPL-3.0',
        'mpl': 'MPL',
        'mpl 2.0': 'MPL-2.0',
        'mozilla public license': 'MPL',
        'isc': 'ISC',
        'isc license': 'ISC',
        'unlicense': 'Unlicense',
        'public domain': 'Public-Domain',
        'proprietary': 'Proprietary',
        'commercial': 'Proprietary',
        'unknown': 'Unknown',
    }
    
    def __init__(self, spdx_licenses: Set[str], fuzzy_threshold: float = 0.85):
        """Initialize matcher.
        
        Args:
            spdx_licenses: Set of known SPDX license identifiers
            fuzzy_threshold: Similarity threshold for fuzzy matching (0-1)
        """
        self.spdx_licenses = spdx_licenses
        self.fuzzy_threshold = fuzzy_threshold
        
        # Build lowercase mapping for case-insensitive lookups
        self._spdx_lower_map = {lic.lower(): lic for lic in spdx_licenses}
    
    def match(self, license_text: str) -> Set[str]:
        """Match license text to SPDX identifiers.
        
        Tries multiple strategies:
        1. SPDX expression parsing (for "MIT OR Apache-2.0", "GPL-2.0+", etc.)
        2. Exact match (case-insensitive)
        3. Normalization
        4. Fuzzy matching
        5. Pattern extraction
        
        Args:
            license_text: Raw license text from package metadata
            
        Returns:
            Set of matched SPDX identifiers
        """
        if not license_text or not license_text.strip():
            return set()
        
        matched = set()
        
        # Strategy 0: Try parsing as SPDX expression
        parsed_licenses = SPDXExpressionParser.parse(license_text)
        if len(parsed_licenses) > 1 or (parsed_licenses and '-or-later' in parsed_licenses[0]):
            # Looks like an SPDX expression, match each part
            for lic in parsed_licenses:
                submatch = self._match_single(lic)
                if submatch:
                    matched.update(submatch)
            if matched:
                return matched
        
        # Single license - use original matching logic
        return self._match_single(license_text)
    
    def _match_single(self, license_text: str) -> Set[str]:
        """Match a single license identifier.
        
        Args:
            license_text: Single license identifier
            
        Returns:
            Set of matched SPDX identifiers
        """
        matched = set()
        
        # Strategy 1: Exact match (case-insensitive)
        exact = self._exact_match(license_text)
        if exact:
            matched.update(exact)
        
        # Strategy 2: Normalization
        normalized = self._normalize(license_text)
        if normalized:
            matched.add(normalized)
        
        # Strategy 3: Check if any SPDX license is contained in text
        contained = self._find_contained(license_text)
        if contained:
            matched.update(contained)
        
        # Strategy 4: Fuzzy matching (only if nothing found yet)
        if not matched:
            fuzzy = self._fuzzy_match(license_text)
            if fuzzy:
                matched.add(fuzzy)
        
        return matched
    
    def _exact_match(self, text: str) -> Set[str]:
        """Try exact case-insensitive match."""
        text_lower = text.strip().lower()
        
        # Check if it's an exact SPDX identifier
        if text_lower in self._spdx_lower_map:
            return {self._spdx_lower_map[text_lower]}
        
        # Check for multiple licenses separated by common delimiters
        # Handle: "MIT OR Apache-2.0", "MIT / BSD", "MIT, Apache"
        separators = [' or ', ' and ', ' / ', ', ', ';']
        for sep in separators:
            if sep in text_lower:
                parts = [p.strip() for p in text_lower.split(sep)]
                matches = set()
                for part in parts:
                    if part in self._spdx_lower_map:
                        matches.add(self._spdx_lower_map[part])
                if matches:
                    return matches
        
        return set()
    
    def _normalize(self, text: str) -> Optional[str]:
        """Normalize common license name variations."""
        text_lower = text.strip().lower()
        
        # Direct lookup
        if text_lower in self.NORMALIZATIONS:
            normalized = self.NORMALIZATIONS[text_lower]
            # Check if normalized form is in SPDX
            if normalized.lower() in self._spdx_lower_map:
                return self._spdx_lower_map[normalized.lower()]
            return normalized
        
        # Try removing common prefixes/suffixes
        cleaned = re.sub(r'\s+license\s*$', '', text_lower)
        cleaned = re.sub(r'^the\s+', '', cleaned)
        
        if cleaned in self.NORMALIZATIONS:
            normalized = self.NORMALIZATIONS[cleaned]
            if normalized.lower() in self._spdx_lower_map:
                return self._spdx_lower_map[normalized.lower()]
            return normalized
        
        return None
    
    def _find_contained(self, text: str) -> Set[str]:
        """Find SPDX licenses contained in text."""
        matched = set()
        text_upper = text.upper()
        
        # Look for SPDX identifiers in the text
        for spdx_lic in self.spdx_licenses:
            # Check if SPDX license appears in text
            if spdx_lic.upper() in text_upper:
                matched.add(spdx_lic)
        
        return matched
    
    def _fuzzy_match(self, text: str) -> Optional[str]:
        """Fuzzy match to find closest SPDX license."""
        text_lower = text.strip().lower()
        
        best_match = None
        best_ratio = 0.0
        
        for spdx_lower, spdx_original in self._spdx_lower_map.items():
            ratio = SequenceMatcher(None, text_lower, spdx_lower).ratio()
            if ratio > best_ratio and ratio >= self.fuzzy_threshold:
                best_ratio = ratio
                best_match = spdx_original
        
        return best_match
    
    def normalize_license_set(self, licenses: Set[str]) -> Set[str]:
        """Normalize a set of license identifiers.
        
        Args:
            licenses: Set of raw license identifiers
            
        Returns:
            Set of normalized SPDX identifiers
        """
        normalized = set()
        for lic in licenses:
            matched = self.match(lic)
            if matched:
                normalized.update(matched)
            else:
                # Keep original if no match found
                normalized.add(lic)
        
        return normalized
