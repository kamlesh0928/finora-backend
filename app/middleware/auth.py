import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User

# Load environment variables
load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))
    expire = datetime.now(timezone.utc) + timedelta(minutes=jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}
    
    jwt_secret = os.getenv("JWT_SECRET", "change-me-to-a-random-secret-key")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    
    return jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)


def decode_access_token(token: str) -> dict:
    jwt_secret = os.getenv("JWT_SECRET", "change-me-to-a-random-secret-key")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency — extracts and validates JWT, returns the User row."""
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    return user
