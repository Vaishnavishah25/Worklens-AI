# api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.repositories.user_repo import EmployeeRepository
from database.session import get_db

from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from core.config import settings
from auth.password import verify_password

router = APIRouter(prefix="/auth", tags=["Authentication Layer"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = EmployeeRepository(db)
    user = await repo.get_by_email(payload.email)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect authentication credentials")

    now = datetime.now(timezone.utc)

    access_token = jwt.encode({"sub": user.email, "exp": now + timedelta(hours=8)}, settings.JWT_SECRET, algorithm="HS256")
    refresh_token = jwt.encode({"sub": user.email, "exp": now + timedelta(days=7)}, settings.JWT_SECRET, algorithm="HS256")
    
    return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {"id": user.id, "role": user.role, "full_name": user.full_name}
        }

# Backend logic endpoint supporting Token Refresh Flow
@router.post("/refresh")
async def refresh_session_tokens(payload: TokenRefreshRequest):
    try:
        data = jwt.decode(payload.refresh_token, settings.JWT_SECRET, algorithms=["HS256"])
        user_email = data.get("sub")

        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid refresh token payloads")
        
        now = datetime.now(timezone.utc)
        new_access = jwt.encode({"sub": user_email, "exp": datetime.now(timezone.utc) + timedelta(hours=2)}, settings.JWT_SECRET, algorithm="HS256")
        return {"access_token": new_access, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or completely corrupted")