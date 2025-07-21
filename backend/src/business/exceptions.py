# Business module exceptions
from core.exceptions import BaseNotFoundError, BaseValidationError, BaseBadRequestError

class BusinessNotFoundError(BaseNotFoundError):
    pass

class BusinessSettingsNotFoundError(BaseNotFoundError):
    """Raised when business settings are not found"""
    pass

class BusinessSettingsValidationError(BaseValidationError):
    """Raised when business settings validation fails"""
    pass

class TaxConfigurationNotFoundError(BaseNotFoundError):
    """Raised when a tax configuration is not found"""
    pass

class BusinessValidationError(BaseValidationError):
    """Raised when business data validation fails"""
    pass

class TaxConfigurationValidationError(BaseValidationError):
    """Raised when tax configuration validation fails"""
    pass

class DuplicateTaxConfigurationError(BaseBadRequestError):
    """Raised when trying to create a tax configuration that already exists"""
    pass

class InvalidTaxRateError(BaseBadRequestError):
    """Raised when tax rate is invalid"""
    pass

class BusinessSettingsUpdateError(BaseBadRequestError):
    """Raised when business settings update fails"""
    pass

class TaxConfigurationUpdateError(BaseBadRequestError):
    """Raised when tax configuration update fails"""
    pass

class TaxConfigurationDeleteError(BaseBadRequestError):
    """Raised when tax configuration deletion fails"""
    pass 