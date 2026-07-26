from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_auth_service, get_registration_service
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginWithOTPRequest,
    PreLoginRequest,
    PreLoginResponse,
    ResetPasswordWithOTPRequest,
    SetInitialPasswordRequest,
    StaffCreate,
    Token,
    UserRead,
)
from app.security.auth import create_access_token, get_current_user
from app.security.rbac import require_role
from app.services.auth_service import AuthService
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_info(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    device = request.headers.get("user-agent")
    return ip, device


async def _issue_token(user: User, service: AuthService) -> Token:
    full_name = await service.get_full_name(user)
    return Token(
        access_token=create_access_token(subject=user.email, role=user.role),
        role=user.role,
        email=user.email,
        full_name=full_name,
        must_change_password=user.must_change_password,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_staff(
    payload: StaffCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    service: RegistrationService = Depends(get_registration_service),
    admin: User = Depends(require_role("admin")),
):
    ip, _ = _client_info(request)
    return await service.create_staff(payload, actor_user_id=admin.id, background_tasks=background_tasks, ip_address=ip)


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    ip, device = _client_info(request)
    user = await service.login(form_data.username, form_data.password, ip, device)
    return await _issue_token(user, service)


@router.get("/me", response_model=UserRead)
async def me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    full_name = await service.get_full_name(current_user)
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        full_name=full_name,
        is_active=current_user.is_active,
        must_change_password=current_user.must_change_password,
    )


@router.post("/change-password", response_model=UserRead)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return await service.change_password(current_user, payload.current_password, payload.new_password)


@router.post("/set-initial-password", response_model=Token)
async def set_initial_password(
    payload: SetInitialPasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Completes the first-login OTP flow: the OTP already proved identity
    (see /auth/login-with-otp), so no current_password is required here."""
    user = await service.set_initial_password(current_user, payload.new_password)
    return await _issue_token(user, service)


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    await service.forgot_password(payload.email, background_tasks)
    return {"detail": "If that email exists, an OTP has been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordWithOTPRequest,
    service: AuthService = Depends(get_auth_service),
):
    await service.reset_password(payload.email, payload.otp, payload.new_password)
    return {"detail": "Password successfully reset"}


@router.post("/pre-login", response_model=PreLoginResponse)
async def pre_login(
    payload: PreLoginRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    return await service.pre_login(payload.email, background_tasks)


@router.post("/login-with-otp", response_model=Token)
async def login_with_otp(
    payload: LoginWithOTPRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    ip, device = _client_info(request)
    user = await service.login_with_otp(payload.email, payload.otp, ip, device)
    return await _issue_token(user, service)
