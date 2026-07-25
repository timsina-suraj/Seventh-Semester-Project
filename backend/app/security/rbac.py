"""Role-based access control dependency factory.

Usage:
    @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
"""
from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.security.auth import get_current_user


def require_role(*allowed_roles: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.must_change_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PASSWORD_CHANGE_REQUIRED: set a new password before continuing (POST /auth/change-password)",
            )
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted to access this resource",
            )
        return current_user

    return dependency