"""Domain errors. Services raise these; main.py turns them into JSON responses."""


class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class InvalidReferenceError(AppError):
    """A request body points at a resource that does not exist."""
    status_code = 422
    code = "invalid_reference"
