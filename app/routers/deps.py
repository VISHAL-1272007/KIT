"""
Shared dependency – extract and validate the current user from the JWT token.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.schemas import TokenData
from app.models.store import USERS
from app.services.auth_service import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    token_data = decode_token(token)
    if token_data is None or token_data.user_id not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data
