class PermitCheckError(Exception):
    """Base class for all PermitCheck exceptions."""
    def __init__(self, message=None):
        super().__init__(message or "PermitCheck: license compliance check failed.")


class PermitCheckWarning(Warning):
    """Warning message for PermitCheck license compliance."""
    def __init__(self, message=None):
        super().__init__(message or "PermitCheck: License compliance warning.")


class PermitCheckInfo:
    """Informational message for PermitCheck license compliance."""
    def __init__(self, message=None):
        self.message = message or "PermitCheck: License compliance successful."

    def __str__(self):
        return self.message


# New specific exceptions for better error handling
class ConfigurationError(PermitCheckError):
    """Raised when configuration is invalid or missing."""
    pass


class PluginLoadError(PermitCheckError):
    """Raised when a plugin fails to load."""
    pass


class DependencyNotFoundError(PermitCheckError):
    """Raised when a dependency cannot be found."""
    pass


class LicenseNotFoundError(PermitCheckError):
    """Raised when a license cannot be determined."""
    pass


class InvalidLicenseError(PermitCheckError):
    """Raised when a license is invalid or not allowed."""
    pass