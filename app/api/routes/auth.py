from fastapi import HTTPException, status, Depends
from fastapi import APIRouter

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.db.session import get_db

pwd_context = CryptContext(schemes=["bcrypt"])
router = APIRouter(prefix="/auth", tags=["auth"])

def create_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@router.post('/register')
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:

    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=str(user_data.email),
        hashed_password=pwd_context.hash(user_data.password),
        created_at=datetime.now(timezone.utc)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(id=new_user.id, email=new_user.email, created_at=new_user.created_at)


@router.post('/login')
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_token(str(user_data.email))

    return TokenResponse(access_token=token, token_type="bearer")