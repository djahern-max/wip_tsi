from datetime import timedelta
from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserLogin
from app.schemas.auth import Token
from app.core.security import verify_password, create_access_token
from app.core.config import settings

if TYPE_CHECKING:
    from app.dependencies import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticate user and return JWT token
    """
    # Find user by username (which is email address)
    user = db.query(User).filter(User.username == user_credentials.username).first()

    # Check if user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.post("/verify-token")
async def verify_token_endpoint(
    db: Session = Depends(get_db), credentials: HTTPBearer = Depends(security)
):
    """
    Verify that the provided token is valid and return user info
    """
    from app.dependencies import get_current_user

    current_user = get_current_user(credentials, db)

    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active,
        },
    }
