# Business module exceptions
from ..core.shared.exceptions import NotFoundError, ValidationError, BadRequestError

class BusinessNotFoundError(NotFoundError):
    pass

class BusinessSettingsNotFoundError(NotFoundError):
    """Raised when business settings are not found"""
    pass

class BusinessSettingsValidationError(ValidationError):
    """Raised when business settings validation fails"""
    pass

class TaxConfigurationNotFoundError(NotFoundError):
    """Raised when a tax configuration is not found"""
    pass

class BusinessValidationError(ValidationError):
    """Raised when business data validation fails"""
    pass

class TaxConfigurationValidationError(ValidationError):
    """Raised when tax configuration validation fails"""
    pass

class DuplicateTaxConfigurationError(BadRequestError):
    """Raised when trying to create a tax configuration that already exists"""
    pass

class InvalidTaxRateError(BadRequestError):
    """Raised when tax rate is invalid"""
    pass

class BusinessSettingsUpdateError(BadRequestError):
    """Raised when business settings update fails"""
    pass

class TaxConfigurationUpdateError(BadRequestError):
    """Raised when tax configuration update fails"""
    pass

class TaxConfigurationDeleteError(BadRequestError):
    """Raised when tax configuration deletion fails"""
    pass 