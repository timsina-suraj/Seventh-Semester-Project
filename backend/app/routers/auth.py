import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.doctor import Doctor
from app.models.user import User, VALID_ROLES
from app.schemas.auth import ChangePasswordRequest, Token, UserCreate, UserRead, ForgotPasswordRequest, ResetPasswordWithOTPRequest, PreLoginRequest, PreLoginResponse, LoginWithOTPRequest
from app.services.email_service import send_otp_email, send_password_reset_otp_email
from app.security.auth import (
    create_access_token,
    generate_temp_password,
    get_current_user,
    hash_password,
    verify_password,
)
from app.security.rbac import require_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    # Only an admin may create new accounts 
    _: User = Depends(require_role("admin")),
):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}")
    if payload.role == "patient":
        raise HTTPException(
            status_code=400,
            detail="Patient accounts are created by a receptionist from the patient registration form, "
            "so the login and the patient record are always linked.",
        )
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    import secrets
    temp_password = secrets.token_urlsafe(32)

    user = User(
        email=payload.email,
        password_hash=hash_password(temp_password),
        role=payload.role,
        must_change_password=True,
    )
    db.add(user)
    db.flush()  # get user.id without committing yet

    if payload.role == "doctor":
        # Creating a doctor account always creates the matching Doctor
        # profile row, so "Users" and "Doctors" never fall out of sync.
        db.add(
            Doctor(
                user_id=user.id,
                full_name=payload.full_name or payload.email,
                specialization=payload.specialization or "General Physician",
                encrypted_phone=payload.phone,
                is_available=True,
            )
        )

    db.commit()
    db.refresh(user)
    
    # No email is sent here. OTP will be generated on first login.
    
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(subject=user.email, role=user.role)
    return Token(
        access_token=token,
        role=user.role,
        email=user.email,
        must_change_password=user.must_change_password,
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", response_model=UserRead)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="New password must be different from the current one")

    current_user.password_hash = hash_password(payload.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal if user exists or not for security reasons, just return ok.
        return {"detail": "If that email exists, an OTP has been sent."}
    
    otp = generate_temp_password()
    user.reset_otp = hash_password(otp)
    
    from datetime import datetime, timedelta, timezone
    user.reset_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    db.commit()
    
    send_password_reset_otp_email(user.email, otp)
    return {"detail": "If that email exists, an OTP has been sent."}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordWithOTPRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")
        
    if not user.reset_otp or not user.reset_otp_expires_at:
        raise HTTPException(status_code=400, detail="No active password reset request")
        
    from datetime import datetime, timezone

    expiry = user.reset_otp_expires_at
    
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Reset OTP has expired")
    if not verify_password(payload.otp, user.reset_otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.reset_otp = None
    user.reset_otp_expires_at = None
    db.commit()
    
    return {"detail": "Password successfully reset"}


@router.post("/pre-login", response_model=PreLoginResponse)
def pre_login(
    payload: PreLoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Prevent user enumeration by pretending standard password is required
        return {"requires_otp": False, "requires_password": True}
        
    if user.must_change_password:
        otp = generate_temp_password()
        user.login_otp = hash_password(otp)
        
        from datetime import datetime, timedelta, timezone
        user.login_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.commit()
        
        send_otp_email(user.email, otp)
        return {"requires_otp": True, "requires_password": False}
        
    return {"requires_otp": False, "requires_password": True}


@router.post("/login-with-otp", response_model=Token)
def login_with_otp(
    payload: LoginWithOTPRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or OTP",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        
    if not user.must_change_password:
        raise HTTPException(status_code=400, detail="User has already set a password. Use standard login.")
        
    if not user.login_otp or not user.login_otp_expires_at:
        raise HTTPException(status_code=400, detail="No OTP requested")
        
    from datetime import datetime, timezone
    expiry = user.login_otp_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="OTP has expired")
        
    if not verify_password(payload.otp, user.login_otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or OTP",
        )
        
    # Clear OTP after successful login
    user.login_otp = None
    user.login_otp_expires_at = None
    db.commit()
    
    token = create_access_token(subject=user.email, role=user.role)
    return Token(
        access_token=token,
        role=user.role,
        email=user.email,
        must_change_password=user.must_change_password,
    )
