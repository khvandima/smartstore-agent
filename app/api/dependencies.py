from fastapi import HTTPException, status, Depends
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from app.config import settings

from app.db.models import User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):

    try:
        email = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"]).get("sub")
    except JWTError:
        raise HTTPException(status_code=401)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
