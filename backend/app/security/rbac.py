"""Role-based access control dependency factory.

Usage:
    @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
"""
from fastapi import Depends

from app.core.exceptions import ForbiddenError, PasswordChangeRequiredError
from app.models.user import User
from app.security.auth import get_current_user


def require_role(*allowed_roles: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.must_change_password:
            raise PasswordChangeRequiredError()
        if current_user.role not in allowed_roles:
            raise ForbiddenError(f"Role '{current_user.role}' is not permitted to access this resource")
        return current_user

    return dependency
