# Business module exceptions

class BusinessSettingsNotFoundError(Exception):
    """Raised when business settings are not found"""
    pass

class BusinessSettingsValidationError(Exception):
    """Raised when business settings validation fails"""
    pass

class TaxConfigurationNotFoundError(Exception):
    """Raised when a tax configuration is not found"""
    pass

class BusinessValidationError(Exception):
    """Raised when business data validation fails"""
    pass

class TaxConfigurationValidationError(Exception):
    """Raised when tax configuration validation fails"""
    pass

class DuplicateTaxConfigurationError(Exception):
    """Raised when trying to create a tax configuration that already exists"""
    pass

class InvalidTaxRateError(Exception):
    """Raised when tax rate is invalid"""
    pass

class BusinessSettingsUpdateError(Exception):
    """Raised when business settings update fails"""
    pass

class TaxConfigurationUpdateError(Exception):
    """Raised when tax configuration update fails"""
    pass

class TaxConfigurationDeleteError(Exception):
    """Raised when tax configuration deletion fails"""
    pass 