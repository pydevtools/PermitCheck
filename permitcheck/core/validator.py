"""License validation logic for PermitCheck."""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from enum import Enum

from permitcheck.core.config import LicensePolicy


class Classification(Enum):
    """License classification types."""
    ALLOWED = "allowed"
    ERROR = "error"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class ValidationResult:
    """Result of license validation."""
    allowed: Set[str] = field(default_factory=set)
    errors: Set[str] = field(default_factory=set)
    warnings: Set[str] = field(default_factory=set)
    skipped: Set[str] = field(default_factory=set)
    
    @property
    def has_errors(self) -> bool:
        """Check if validation found errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation found warnings."""
        return len(self.warnings) > 0
    
    @property
    def is_success(self) -> bool:
        """Check if validation passed completely."""
        return not self.has_errors and not self.has_warnings
    
    @property
    def total_checked(self) -> int:
        """Total number of dependencies checked."""
        return len(self.allowed) + len(self.errors) + len(self.warnings)


class LicenseValidator:
    """Validates licenses against policy."""
    
    def __init__(self, policy: LicensePolicy):
        self.policy = policy
    
    def validate(self, dependencies: Dict[str, Set[str]]) -> ValidationResult:
        """Validate all dependencies against policy.
        
        Args:
            dependencies: Dict mapping package names to sets of licenses
            
        Returns:
            ValidationResult with categorized packages
        """
        if not dependencies:
            return ValidationResult()
        
        result = ValidationResult()
        
        # Classify each dependency
        classifications = {}
        for pkg_name, licenses in dependencies.items():
            classification = self._classify_dependency(pkg_name, licenses)
            classifications[pkg_name] = classification
            
            if classification == Classification.ALLOWED:
                result.allowed.add(pkg_name)
            elif classification == Classification.ERROR:
                result.errors.add(pkg_name)
            elif classification == Classification.WARNING:
                result.warnings.add(pkg_name)
            elif classification == Classification.SKIP:
                result.skipped.add(pkg_name)
        
        # If no trigger_error_licenses configured, warnings become errors
        if not self.policy.trigger_error_licenses:
            result.errors |= result.warnings
            result.warnings = set()
        
        return result
    
    def _classify_dependency(self, pkg_name: str, licenses: Set[str]) -> Classification:
        """Classify a single dependency based on its licenses.
        
        Args:
            pkg_name: Package name
            licenses: Set of license identifiers
            
        Returns:
            Classification enum value
        """
        if pkg_name in self.policy.skip_libraries:
            return Classification.SKIP
        
        # Check for trigger error licenses first
        for lic in licenses:
            if lic in self.policy.trigger_error_licenses:
                return Classification.ERROR
        
        # Check for allowed licenses
        for lic in licenses:
            if lic in self.policy.allowed_licenses:
                return Classification.ALLOWED
        
        # If no error and no allowed, it's a warning
        return Classification.WARNING
    
    def get_classification(self, pkg_name: str, licenses: Set[str]) -> Classification:
        """Public method to get classification for a single package."""
        return self._classify_dependency(pkg_name, licenses)
