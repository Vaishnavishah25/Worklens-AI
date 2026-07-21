# backend/auth/middleware.py

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from auth.token import decode_token
from services.user_service import UserService
from database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_authenticated_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token, expected_type="access")
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
        
    user_service = UserService(db)
    user = await user_service.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
        
    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = [r.lower() for r in allowed_roles]

    def __call__(self, current_user = Depends(get_authenticated_user)):
        if str(current_user.role).lower() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient permission level."
            )
        return current_user