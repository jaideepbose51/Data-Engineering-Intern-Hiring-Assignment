class PipelineError(Exception):
    """Base class for pipeline errors."""


class DataValidationError(PipelineError):
    """Raised when input or output data fails validation."""
