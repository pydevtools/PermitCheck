"""Core functionality for PermitCheck."""

from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.core.validator import LicenseValidator, ValidationResult, Classification
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.cache import LicenseCache, CacheEntry
from permitcheck.core.matcher import LicenseMatcher

__all__ = [
    'ConfigManager',
    'LicensePolicy',
    'LicenseValidator',
    'ValidationResult',
    'Classification',
    'Reporter',
    'OutputFormat',
    'LicenseCache',
    'CacheEntry',
    'LicenseMatcher',
]
