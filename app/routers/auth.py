"""
Authentication router – login and token endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import LoginRequest, Token
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
def login(request: LoginRequest):
    """
    Authenticate a logistics worker and return a JWT access token.
    The token should be included as a Bearer token in subsequent requests.
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
        }
    )
    return Token(access_token=token)
