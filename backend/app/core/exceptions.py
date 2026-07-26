"""Domain exceptions raised by the service layer.

Services never raise `HTTPException` directly (that would couple business
logic to FastAPI/HTTP). Instead they raise one of these, and a single
exception handler registered in `main.py` translates it to an HTTP
response. Each exception carries its own `status_code` as plain metadata —
this keeps the exception classes importable and testable without FastAPI,
while still avoiding a giant if/elif mapping table in `main.py`.
"""
from __future__ import annotations


class AppError(Exception):
    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class EmailAlreadyExistsError(AppError):
    status_code = 400

    def __init__(self, email: str):
        super().__init__(f"An account with email '{email}' already exists")


class InvalidCredentialsError(AppError):
    status_code = 401

    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(detail)


class AccountDisabledError(AppError):
    status_code = 403

    def __init__(self, detail: str = "Account is disabled"):
        super().__init__(detail)


class PasswordChangeRequiredError(AppError):
    status_code = 403

    def __init__(self):
        super().__init__(
            "PASSWORD_CHANGE_REQUIRED: set a new password before continuing "
            "(POST /auth/change-password)"
        )


class OtpError(AppError):
    status_code = 400


class OtpNotRequestedError(OtpError):
    def __init__(self):
        super().__init__("No OTP has been requested for this account")


class OtpExpiredError(OtpError):
    def __init__(self):
        super().__init__("OTP has expired")


class OtpInvalidError(OtpError):
    def __init__(self):
        super().__init__("Incorrect OTP")


class OtpAttemptsExceededError(OtpError):
    def __init__(self):
        super().__init__("Too many incorrect attempts — request a new OTP")


class RateLimitedError(AppError):
    status_code = 429

    def __init__(self, detail: str = "Too many requests — please wait before trying again"):
        super().__init__(detail)


class ValidationError(AppError):
    status_code = 422
