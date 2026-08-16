from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.postgres import get_db
from models.models import User
from models.schemas import UserResponse, UserCreate
from authentication.jwt import get_current_user, get_password_hash
from authentication.roles import require_admin, require_quality_manager
from services.db_service import list_users, get_user_by_id, create_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
def get_users_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quality_manager)
):
    """
    List all registered users in the system.
    """
    return list_users(db)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Directly create a new user account (Admin restricted).
    """
    # Check duplicate
    existing = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered."
        )
    return create_user(db, payload)

@router.patch("/{user_id}", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a user's role (Admin restricted).
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    role = payload.get("role")
    if role:
        if role not in ["admin", "quality_manager", "factory_supervisor", "quality_engineer", "operator"]:
            raise HTTPException(status_code=400, detail="Invalid role type.")
        db_user.role = role
        db.commit()
        db.refresh(db_user)
        
    return db_user

@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset a user's password (Allowed if self-update OR admin).
    """
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{current_user.role}' has insufficient permissions. Required: ['admin'] or self."
        )
        
    password = payload.get("password")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
        
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    db_user.hashed_password = get_password_hash(password)
    db.commit()
    return {"message": "User password reset successfully."}
