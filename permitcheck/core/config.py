"""Configuration management for PermitCheck."""

import os
from dataclasses import dataclass, field
from typing import Set, Optional, Dict, Any
from pathlib import Path

from permitcheck.utils import read_yaml, read_toml
from permitcheck.exceptions import ConfigurationError


@dataclass
class LicensePolicy:
    """License policy configuration."""
    allowed_licenses: Set[str] = field(default_factory=set)
    trigger_error_licenses: Set[str] = field(default_factory=set)
    skip_libraries: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Add base license identifiers after initialization."""
        # Add base identifiers (e.g., "Apache" from "Apache-2.0")
        self.allowed_licenses |= {lic.split('-')[0] for lic in self.allowed_licenses}
        self.trigger_error_licenses |= {lic.split('-')[0] for lic in self.trigger_error_licenses}
    
    def validate(self) -> None:
        """Validate policy for conflicts."""
        conflicts = self.allowed_licenses & self.trigger_error_licenses
        if conflicts:
            raise ConfigurationError(
                f"Conflicting licenses: {conflicts} cannot be both allowed and trigger errors"
            )


class ConfigManager:
    """Manages configuration loading from various sources."""
    
    CONFIG_FILES = ['permitcheck.yaml', '.permitcheck.yaml', 'permitcheck.yml']
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()
    
    def load_policy(self, settings: Optional[tuple] = None) -> LicensePolicy:
        """Load license policy from settings tuple or config file.
        
        Args:
            settings: Optional tuple of (allowed, trigger_error, skip_libraries)
            
        Returns:
            LicensePolicy instance
            
        Raises:
            ConfigurationError: If configuration is invalid or not found
        """
        if settings:
            allowed, trigger_error, skip = settings
            policy = LicensePolicy(
                allowed_licenses=allowed,
                trigger_error_licenses=trigger_error,
                skip_libraries=skip
            )
            policy.validate()
            return policy
        
        # Try to load from config file
        config_path = self._find_config_file()
        if not config_path:
            raise ConfigurationError(
                f"No configuration file found in {self.base_dir}. "
                f"Expected one of: {', '.join(self.CONFIG_FILES)}"
            )
        
        config = self._load_config(config_path)
        return self._parse_policy(config)
    
    def _find_config_file(self) -> Optional[Path]:
        """Find first existing config file."""
        for filename in self.CONFIG_FILES:
            config_path = self.base_dir / filename
            if config_path.exists():
                return config_path
        return None
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if config_path.suffix in ['.yaml', '.yml']:
                return read_yaml(str(config_path))
            elif config_path.suffix == '.toml':
                return read_toml(str(config_path))
            else:
                raise ConfigurationError(f"Unsupported config format: {config_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load {config_path}: {e}")
    
    def _parse_policy(self, config: Dict[str, Any]) -> LicensePolicy:
        """Parse policy from config dictionary."""
        if not isinstance(config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        policy = LicensePolicy(
            allowed_licenses=set(config.get('allowed_licenses', [])),
            trigger_error_licenses=set(config.get('trigger_error_licenses', [])),
            skip_libraries=set(config.get('skip_libraries', []) or [])
        )
        
        policy.validate()
        return policy
    
    def load_from_pyproject(self) -> Optional[LicensePolicy]:
        """Load policy from pyproject.toml [licenses] section."""
        pyproject_path = self.base_dir / 'pyproject.toml'
        if not pyproject_path.exists():
            return None
        
        try:
            config = read_toml(str(pyproject_path))
            if 'licenses' not in config:
                return None
            
            licenses_config = config['licenses']
            policy = LicensePolicy(
                allowed_licenses=set(licenses_config.get('allowed', [])),
                trigger_error_licenses=set(licenses_config.get('trigger_error', [])),
                skip_libraries=set(licenses_config.get('skip_libraries', []))
            )
            policy.validate()
            return policy
        except Exception as e:
            raise ConfigurationError(f"Failed to load from pyproject.toml: {e}")
