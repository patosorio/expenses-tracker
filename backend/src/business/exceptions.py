# Business-specific exceptions
from ..core.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError
)


# Business Settings Exceptions
class BusinessSettingsNotFoundError(NotFoundError):
    """Business settings not found in database."""
    detail: str = "Business settings not found"
    error_code: str = "BUSINESS_SETTINGS_NOT_FOUND"


class BusinessSettingsValidationError(ValidationError):
    """Business settings data validation failed."""
    detail: str = "Invalid business settings data"
    error_code: str = "BUSINESS_SETTINGS_VALIDATION_FAILED"


class BusinessSettingsUpdateError(BadRequestError):
    """Business settings update operation failed."""
    detail: str = "Failed to update business settings"
    error_code: str = "BUSINESS_SETTINGS_UPDATE_FAILED"


class BusinessSettingsAlreadyExistsError(ConflictError):
    """Business settings already exist for this user."""
    detail: str = "Business settings already exist for this user"
    error_code: str = "BUSINESS_SETTINGS_ALREADY_EXISTS"


# Tax Configuration Exceptions
class TaxConfigurationNotFoundError(NotFoundError):
    """Tax configuration not found in database."""
    detail: str = "Tax configuration not found"
    error_code: str = "TAX_CONFIGURATION_NOT_FOUND"


class TaxConfigurationValidationError(ValidationError):
    """Tax configuration data validation failed."""
    detail: str = "Invalid tax configuration data"
    error_code: str = "TAX_CONFIGURATION_VALIDATION_FAILED"


class TaxConfigurationUpdateError(BadRequestError):
    """Tax configuration update operation failed."""
    detail: str = "Failed to update tax configuration"
    error_code: str = "TAX_CONFIGURATION_UPDATE_FAILED"


class TaxConfigurationDeleteError(BadRequestError):
    """Tax configuration deletion operation failed."""
    detail: str = "Failed to delete tax configuration"
    error_code: str = "TAX_CONFIGURATION_DELETE_FAILED"


class DuplicateTaxConfigurationError(ConflictError):
    """Tax configuration with same name already exists for this user."""
    detail: str = "Tax configuration with this name already exists"
    error_code: str = "DUPLICATE_TAX_CONFIGURATION"


class InvalidTaxRateError(ValidationError):
    """Tax rate value is invalid or out of range."""
    detail: str = "Tax rate must be between 0 and 100 percent"
    error_code: str = "INVALID_TAX_RATE"


class TaxConfigurationInUseError(BadRequestError):
    """Cannot delete/modify tax configuration that is currently in use."""
    detail: str = "Tax configuration is currently in use"
    error_code: str = "TAX_CONFIGURATION_IN_USE"


class DefaultTaxConfigurationError(BadRequestError):
    """Error related to default tax configuration operations."""
    detail: str = "Error with default tax configuration"
    error_code: str = "DEFAULT_TAX_CONFIGURATION_ERROR"


class MultipleDefaultTaxConfigsError(ConflictError):
    """Multiple default tax configurations found for user."""
    detail: str = "Multiple default tax configurations detected"
    error_code: str = "MULTIPLE_DEFAULT_TAX_CONFIGS"


# Business Validation Exceptions
class BusinessValidationError(ValidationError):
    """General business data validation failed."""
    detail: str = "Business data validation failed"
    error_code: str = "BUSINESS_VALIDATION_FAILED"


class InvalidBusinessNameError(ValidationError):
    """Business name is invalid or too long."""
    detail: str = "Business name must be between 1 and 255 characters"
    error_code: str = "INVALID_BUSINESS_NAME"


class InvalidBusinessAddressError(ValidationError):
    """Business address format is invalid."""
    detail: str = "Invalid business address format"
    error_code: str = "INVALID_BUSINESS_ADDRESS"


class InvalidBusinessEmailError(ValidationError):
    """Business email format is invalid."""
    detail: str = "Invalid business email format"
    error_code: str = "INVALID_BUSINESS_EMAIL"


class InvalidBusinessPhoneError(ValidationError):
    """Business phone number format is invalid."""
    detail: str = "Invalid business phone number format"
    error_code: str = "INVALID_BUSINESS_PHONE"


class InvalidTaxNumberError(ValidationError):
    """Business tax number format is invalid."""
    detail: str = "Invalid tax number format"
    error_code: str = "INVALID_TAX_NUMBER"


class InvalidCurrencyError(ValidationError):
    """Invalid currency code for business settings."""
    detail: str = "Invalid currency code"
    error_code: str = "INVALID_CURRENCY"


class InvalidFiscalYearError(ValidationError):
    """Invalid fiscal year configuration."""
    detail: str = "Invalid fiscal year configuration"
    error_code: str = "INVALID_FISCAL_YEAR"


# Tax Configuration Specific Validation Exceptions
class TaxConfigurationNameTooLongError(ValidationError):
    """Tax configuration name exceeds maximum length."""
    detail: str = "Tax configuration name must be 100 characters or less"
    error_code: str = "TAX_CONFIG_NAME_TOO_LONG"


class InvalidTaxTypeError(ValidationError):
    """Invalid tax type specified."""
    detail: str = "Invalid tax type"
    error_code: str = "INVALID_TAX_TYPE"


class TaxConfigurationDescriptionTooLongError(ValidationError):
    """Tax configuration description exceeds maximum length."""
    detail: str = "Tax configuration description must be 500 characters or less"
    error_code: str = "TAX_CONFIG_DESCRIPTION_TOO_LONG"


class TaxRateOutOfRangeError(ValidationError):
    """Tax rate is outside valid range."""
    detail: str = "Tax rate must be between 0 and 100"
    error_code: str = "TAX_RATE_OUT_OF_RANGE"


class TaxRatePrecisionError(ValidationError):
    """Tax rate has too many decimal places."""
    detail: str = "Tax rate can have maximum 4 decimal places"
    error_code: str = "TAX_RATE_PRECISION_ERROR"


# Business Logic Exceptions
class BusinessNotFoundError(NotFoundError):
    """General business entity not found."""
    detail: str = "Business entity not found"
    error_code: str = "BUSINESS_NOT_FOUND"


class BusinessOperationError(BadRequestError):
    """General business operation failed."""
    detail: str = "Business operation failed"
    error_code: str = "BUSINESS_OPERATION_FAILED"


class InvalidBusinessOperationError(BadRequestError):
    """Invalid business operation attempted."""
    detail: str = "Invalid business operation"
    error_code: str = "INVALID_BUSINESS_OPERATION"