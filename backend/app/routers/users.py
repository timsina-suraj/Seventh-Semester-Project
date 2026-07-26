from fastapi import APIRouter, Depends

from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies import get_auth_service, get_user_repository
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRead
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=list[UserRead])
async def list_users(repo: UserRepository = Depends(get_user_repository)):
    return await repo.list()


@router.patch("/{user_id}/toggle-active", response_model=UserRead)
async def toggle_active(user_id: int, repo: UserRepository = Depends(get_user_repository)):
    user = await repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")

    # An admin may re-enable another admin, but may never disable one --
    # including themselves -- otherwise one admin (or a mistaken click)
    # could lock out the rest of the admin team.
    disabling = user.is_active  # True now means this call would turn it off
    if disabling and user.role == "admin":
        raise ForbiddenError("Admins cannot disable another admin account.")

    user.is_active = not user.is_active
    await repo.commit()
    await repo.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=UserRead)
async def admin_reset_password(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """Forces the account back through the first-login OTP flow — see
    AuthService.admin_force_password_reset for why this reuses that path
    instead of a second reset mechanism."""
    user = await repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    await auth_service.admin_force_password_reset(user, current_user.id)
    await repo.refresh(user)
    return user
