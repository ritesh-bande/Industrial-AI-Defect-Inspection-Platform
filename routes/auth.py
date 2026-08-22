from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.postgres import get_db
from models.schemas import UserCreate, UserLogin, Token, UserResponse
from authentication.jwt import create_access_token, get_current_user, get_password_hash, verify_password
from models.models import User
from services.db_service import create_user, get_user_by_username, get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the system.
    Returns the generated JWT access token.
    """
    existing_user = get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered."
        )
    
    existing_email = get_user_by_email(db, user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered."
        )
        
    db_user = create_user(db, user_in)
    token = create_access_token({
        "sub": db_user.username,
        "user_id": db_user.id,
        "email": db_user.email,
        "role": db_user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Log in using username or email and password against the user database.
    Enforces password hash verification and active user status.
    Returns access token and authenticated user info.
    """
    username = payload.username
    email = payload.email
    password = payload.password
    
    if not password or (not username and not email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/email and password are required."
        )

    # Validate email format if provided as email
    target_email = email or (username if "@" in str(username) else None)
    if target_email and "@" not in target_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )
        
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user:
        identifier = email or username
        user = get_user_by_username(db, identifier)
    if not user and target_email:
        user = get_user_by_email(db, target_email)

    # 1. Reject non-existent user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # 2. Reject incorrect password hash match
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # 3. Reject inactive/disabled user account
    if hasattr(user, "is_active") and user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled."
        )
        
    token = create_access_token({
        "sub": user.username,
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current authenticated user profile.
    """
    return current_user

import secrets
import hashlib
from datetime import datetime, timedelta
from models.schemas import ForgotPasswordRequest, ResetPasswordRequest
from models.models import PasswordResetToken
from utils.email import send_password_reset_email

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generates a secure single-use password reset token and sends a reset link.
    Always returns generic message to prevent email enumeration.
    """
    email = payload.email.lower().strip()
    user = get_user_by_email(db, email)
    
    if user and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None
        ).update({"used_at": datetime.utcnow()})
        
        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(reset_record)
        db.commit()
        
        send_password_reset_email(user.email, raw_token)
        
    return {
        "message": "If an account exists for this email, a password reset link has been sent."
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets user password using a valid single-use token.
    Updates password hash in DB and invalidates the token.
    """
    raw_token = payload.token.strip()
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )
        
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )
        
    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )
        
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )
        
    user.hashed_password = get_password_hash(payload.new_password)
    token_record.used_at = datetime.utcnow()
    
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at == None
    ).update({"used_at": datetime.utcnow()})
    
    db.commit()
    
    return {
        "message": "Your password has been reset successfully."
    }
