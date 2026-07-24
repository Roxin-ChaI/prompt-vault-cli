"""Application-specific exceptions for Prompt Vault CLI."""


class VaultError(Exception):
    """Base exception for application errors."""


class ValidationError(VaultError):
    """Raised when prompt data is invalid."""


class DuplicatePromptError(VaultError):
    """Raised when a prompt name already exists."""


class PromptNotFoundError(VaultError):
    """Raised when a requested prompt does not exist."""


class StorageError(VaultError):
    """Raised when prompt data cannot be read or written."""
