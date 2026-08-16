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
    token = create_access_token({"sub": db_user.username})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Log in using username or email and password.
    Returns access token and user info.
    """
    # Extract identifiers
    username = payload.username
    email = payload.email
    password = payload.password
    
    if not username and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either username or email must be provided."
        )
        
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user:
        identifier = email or username
        user = get_user_by_username(db, identifier)
        
    if not user:
        # Auto-provision new user on first sign-in attempt
        target_email = email or f"{username}@visioninspect.ai"
        target_username = username or (email.split("@")[0] if "@" in email else email)
        new_user_schema = UserCreate(
            username=target_username,
            email=target_email,
            password=password,
            role="quality_engineer"
        )
        user = create_user(db, new_user_schema)
    elif not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )
        
    token = create_access_token({"sub": user.username})
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
