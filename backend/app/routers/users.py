from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRead
from app.security.rbac import require_role

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.patch("/{user_id}/toggle-active", response_model=UserRead)
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # An admin may re-enable another admin, but may never disable one --
    # including themselves -- otherwise one admin (or a mistaken click)
    # could lock out the rest of the admin team.
    disabling = user.is_active  # True now means this call would turn it off
    if disabling and user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Admins cannot disable another admin account.",
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user
