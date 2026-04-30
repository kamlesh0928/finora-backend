from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..middleware.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..models.user import User
from ..schemas.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        auth_provider="email",
        wallet_balance=5000.0,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )

@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate via Google. If user doesn't exist, auto-create.
    The Flutter app sends the Google ID token. In a production environment, 
    this should be verified via Google's OAuth2 API. For the current scope, 
    we authenticate based on the client-provided profile information.
    """
    email = body.email
    if not email:
        raise HTTPException(status_code=400, detail="Email is required from Google auth")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        if not body.is_signup:
            raise HTTPException(status_code=404, detail="User not found")
            
        user = User(
            email=email,
            name=body.name or email.split("@")[0],
            auth_provider="google",
            wallet_balance=5000.0,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        if body.is_signup:
            pass
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()

    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    In a production application, a password reset email would be dispatched.
    Currently, we return a success message for any valid account request.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        return MessageResponse(message="If the email exists, a reset link has been sent.")

    return MessageResponse(message="If the email exists, a reset link has been sent.")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Demo endpoint: Directly resets the user's password without an OTP for demo purposes.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    
    return MessageResponse(message="Password reset successfully")

@router.post("/logout", response_model=MessageResponse)
async def logout(user: User = Depends(get_current_user)):
    """
    Client-side logout acknowledgment. Note: In production, the access token 
    should be added to a server-side revocation list (blocklist).
    """
    return MessageResponse(message="Logged out successfully")
