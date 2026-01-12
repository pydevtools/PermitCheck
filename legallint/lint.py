import os
from typing import Dict, Set, Optional, Tuple
from legallint.utils import read_yaml, exit
from legallint.exceptions import (
    PermitCheckError, 
    PermitCheckWarning, 
    PermitCheckInfo,
    ConfigurationError
)

class Settings:
    basedir = os.getcwd()
    allowed_licenses: Set[str] = set()
    trigger_error_licenses: Set[str] = set()
    skip_libraries: Set[str] = set()

    config_file = 'permitcheck.yaml'

    @classmethod
    def load(cls, settings: Optional[Tuple[Set[str], Set[str], Set[str]]]) -> None:
        """Load settings from tuple or config file."""
        if (not settings) and (not os.path.isfile(f"{cls.basedir}/{cls.config_file}")):
            raise ConfigurationError(
                f"No {cls.config_file} found in {cls.basedir}. "
                "Please create a configuration file or provide settings."
            )

        if not settings:
            try:
                config = read_yaml(f"{cls.basedir}/{cls.config_file}")
                cls._validate_config(config)
                cls.allowed_licenses = set(config.get('allowed_licenses', []))
                cls.trigger_error_licenses = set(config.get('trigger_error_licenses', []))
                cls.skip_libraries = set(config.get('skip_libraries', []) or [])
            except Exception as e:
                raise ConfigurationError(f"Failed to load configuration: {e}")

        if settings:
            cls.allowed_licenses, cls.trigger_error_licenses, cls.skip_libraries = settings

        # Add base license identifiers (e.g., "Apache" from "Apache-2.0")
        cls.allowed_licenses |= {key.split('-')[0] for key in cls.allowed_licenses}
        cls.trigger_error_licenses |= {key.split('-')[0] for key in cls.trigger_error_licenses}
    
    @classmethod
    def _validate_config(cls, config: Dict) -> None:
        """Validate configuration file contents."""
        if not isinstance(config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        # Check for conflicting licenses
        if 'allowed_licenses' in config and 'trigger_error_licenses' in config:
            allowed = set(config['allowed_licenses'])
            errors = set(config['trigger_error_licenses'])
            conflicts = allowed & errors
            if conflicts:
                raise ConfigurationError(
                    f"Conflicting licenses in configuration: {conflicts} "
                    "cannot be both allowed and trigger errors"
                )

class PermitCheck:
    def __init__(self, deps: Optional[Dict[str, Set[str]]], settings: Optional[Tuple[Set[str], Set[str], Set[str]]] = None) -> None:
        Settings.load(settings)
        self.allowed: Set[str] = set()
        self.errors: Set[str] = set()
        self.warnings: Set[str] = set()
        self.validate(deps)

    def _classify_dependency(self, dep_name: str, license_set: set) -> str:
        """Classify a single dependency based on its licenses.
        
        Returns: 'error', 'allowed', 'warning', or 'skip'
        """
        if dep_name in Settings.skip_libraries:
            return 'skip'
        
        # Check for trigger error licenses
        for lic in license_set:
            if lic in Settings.trigger_error_licenses:
                return 'error'
        
        # Check for allowed licenses
        for lic in license_set:
            if lic in Settings.allowed_licenses:
                return 'allowed'
        
        # If no error and no allowed, it's a warning
        return 'warning'

    def _print_dependency(self, dep_name: str, license_set: set, mark: str):
        """Print a single dependency with its mark."""
        print(f"{mark:<5} {dep_name:<20} {'; '.join(license_set)}")

    def validate(self, deps: Optional[Dict[str, Set[str]]]) -> None:
        """Validate all dependencies against license policies."""
        marks: Dict[str, str] = {
            'allowed': '\u2714',    # check mark
            'error': '\u2716',      # error mark
            'warning': '\u203C',    # warning mark
            'skip': 's'             # skip mark
        }
        
        if deps is None:
            return
        
        # Classify all dependencies
        classifications = {}
        for dep_name, license_set in deps.items():
            classification = self._classify_dependency(dep_name, license_set)
            classifications[dep_name] = classification
            
            if classification == 'allowed':
                self.allowed.add(dep_name)
            elif classification == 'error':
                self.errors.add(dep_name)
            elif classification == 'warning':
                self.warnings.add(dep_name)
        
        # If no trigger_error_licenses configured, warnings become errors
        if not Settings.trigger_error_licenses:
            self.errors |= self.warnings
            self.warnings = set()
        
        # Print all dependencies with their marks
        for dep_name, license_set in deps.items():
            classification = classifications[dep_name]
            mark = marks.get(classification, '')
            self._print_dependency(dep_name, license_set, mark)
        
        # Print summary
        if self.errors:
            print(PermitCheckError())
        elif self.warnings:
            print(PermitCheckWarning())
        else:
            print(PermitCheckInfo())



