# FastAPI dependencies for user authentication and role-based access control.

# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from models.user import User
from sqlalchemy.future import select
from core.config import settings

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

    try:
        # Utilize the product Pydantic config environment variable for the secret key
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid token payloads")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
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