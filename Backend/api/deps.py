# FastAPI dependencies for user authentication and role-based access control.

# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from models.user import User
from sqlalchemy.future import select
from auth.jwt import decode_access_token
from auth.middleware import get_authenticated_user, RoleChecker

role_required = RoleChecker
get_current_user = get_authenticated_user

security = HTTPBearer()

# Fallback for local Hackathon testing when token authorization is bypassed
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    user_email: str = payload.get("sub")
    if user_email is None:
        raise HTTPException(status_code=401, detail="Invalid token payloads")
        
    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def role_required(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Operation not permitted for this security clearance tier"
            )
        return current_user
    return dependency