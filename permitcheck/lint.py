"""Legacy compatibility wrapper for PermitCheck validation.

This module maintains backward compatibility with the original API.
New code should use permitcheck.core modules directly.
"""

import os
from typing import Dict, Set, Optional, Tuple
from pathlib import Path

from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.core.validator import LicenseValidator
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.exceptions import (
    PermitCheckError, 
    PermitCheckWarning, 
    PermitCheckInfo,
    ConfigurationError
)


class Settings:
    """Legacy Settings class for backward compatibility."""
    
    basedir = os.getcwd()
    config_file = 'permitcheck.yaml'
    
    # These will be set by load()
    _config_manager: Optional[ConfigManager] = None
    _policy: Optional[LicensePolicy] = None

    @classmethod
    def load(cls, settings: Optional[Tuple[Set[str], Set[str], Set[str]]]) -> None:
        """Load settings from tuple or config file."""
        cls._config_manager = ConfigManager(Path(cls.basedir))
        cls._policy = cls._config_manager.load_policy(settings)
    
    @classmethod
    def get_policy(cls) -> LicensePolicy:
        """Get loaded policy."""
        if cls._policy is None:
            raise ConfigurationError("Settings not loaded. Call Settings.load() first.")
        return cls._policy


class PermitCheck:
    """Main validation class - legacy API wrapper."""
    
    def __init__(
        self,
        deps: Optional[Dict[str, Set[str]]],
        settings: Optional[Tuple[Set[str], Set[str], Set[str]]] = None,
        output_format: str = "console"
    ) -> None:
        """Initialize and run validation.
        
        Args:
            deps: Dictionary mapping package names to sets of licenses
            settings: Optional tuple of (allowed, trigger_error, skip_libraries)
            output_format: Output format ('console', 'json', 'simple')
        """
        Settings.load(settings)
        policy = Settings.get_policy()
        
        validator = LicenseValidator(policy)
        result = validator.validate(deps or {})
        
        # Store results for backward compatibility
        self.allowed = result.allowed
        self.errors = result.errors
        self.warnings = result.warnings
        
        # Generate report
        format_map = {
            'console': OutputFormat.CONSOLE,
            'json': OutputFormat.JSON,
            'simple': OutputFormat.SIMPLE,
            'html': OutputFormat.HTML,
            'markdown': OutputFormat.MARKDOWN,
            'csv': OutputFormat.CSV,
            'sarif': OutputFormat.SARIF,
        }
        reporter = Reporter(format_map.get(output_format, OutputFormat.CONSOLE))
        reporter.report(result, deps or {}, "python")




