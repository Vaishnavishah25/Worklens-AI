# backend/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from database.session import get_db
from models.user import User
from repositories.user_repo import EmployeeRepository
from auth.password import get_password_hash, verify_password
from auth.jwt import create_access_token
from sqlalchemy import select
from database.base import Base
from database.session import engine
router = APIRouter(prefix="/auth", tags=["Authentication Layer"])

# --- REQUEST/RESPONSE SCHEMAS ---
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, description="User's full name")
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    role: Literal["employee", "mentor", "manager"]
    manager_id: Optional[int] = Field(None, description="Optional ID of their direct mentor/supervisor")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter.")
        return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# --------------------------------------------------------------------------
# Database Initialization
# --------------------------------------------------------------------------

async def init_db():
    """
    Creates all database tables if they do not already exist.
    Called once during FastAPI startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_default_users():
    """
    Seeds default users for demo/development.
    Safe to call multiple times.
    """
    async with AsyncSession(engine) as db:

        repo = EmployeeRepository(db)

        manager = await repo.get_by_email("manager@worklens.ai")
        if manager:
            return

        users = [
            User(
                name="Maya Chen",
                email="manager@worklens.ai",
                password=get_password_hash("manager123"),
                role="manager",
            ),
            User(
                name="Ravi Mehta",
                email="mentor@worklens.ai",
                password=get_password_hash("mentor123"),
                role="mentor",
            ),
            User(
                name="Priya Shah",
                email="employee@worklens.ai",
                password=get_password_hash("employee123"),
                role="employee",
            ),
        ]

        db.add_all(users)
        await db.commit()
        
# --- ENDPOINTS ---

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Dynamically registers new users into the system. Passes passwords through
    the secure native bcrypt hash wrapper before database ingestion.
    """
    repo = EmployeeRepository(db)
    
    # 1. Check if the identity already exists
    existing_user = await repo.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )
    
    # 2. Hash raw credentials securely using native bcrypt
    hashed_password_string = get_password_hash(payload.password)
    
    # 3. Instantiate model mapping directly to verified DB columns
    new_user = User(
        name=payload.name,
        email=payload.email,
        password=hashed_password_string,
        role=payload.role,
        manager_id=payload.manager_id
    )
    
    # 4. Save entity into PostgreSQL
    created_user = await repo.create_user(new_user)
    
    return {
        "message": "User registered successfully",
        "user_id": created_user.id,
        "email": created_user.email,
        "role": created_user.role
    }


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies user identities dynamically against database states, issues
    cryptographically sound access and refresh token blocks.
    """
    repo = EmployeeRepository(db)
    user = await repo.get_by_email(payload.email)

    # Validate user existence and check password hash concurrently
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password credentials"
        )
    token_claims = {
        "sub": user.email,
        "role": user.role,
        "user_id": user.id}

    access_token = create_access_token(data=token_claims)
    refresh_token = create_access_token(data=token_claims, expires_delta=timedelta(days=7))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "role": user.role, 
            "full_name": user.name
        }
    }