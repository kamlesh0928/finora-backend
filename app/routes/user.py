"""User profile routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.achievement import UserAchievement
from ..schemas.schemas import (
    AchievementResponse,
    UpdateGameStateRequest,
    UpdateProfileRequest,
    UserResponse,
)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.role is not None:
        if body.role not in ("Farmer", "Woman", "Student", "Young Adult"):
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Only set initial balance if role is changing/being set for the first time
        if user.role != body.role:
            user.role = body.role
            if body.role == "Farmer":
                user.wallet_balance = 12000.0
            elif body.role == "Woman":
                user.wallet_balance = 8000.0
            elif body.role == "Student":
                user.wallet_balance = 5000.0
            elif body.role == "Young Adult":
                user.wallet_balance = 20000.0
    if body.language is not None:
        if body.language not in ("en", "hi"):
            raise HTTPException(status_code=400, detail="Supported languages: en, hi")
        user.language = body.language

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/game-state", response_model=UserResponse)
async def update_game_state(
    body: UpdateGameStateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's game state fields (wallet, stress, etc.)."""
    if body.wallet_balance is not None:
        user.wallet_balance = max(0, body.wallet_balance)
    if body.emergency_fund is not None:
        user.emergency_fund = max(0, body.emergency_fund)
    if body.stress_level is not None:
        user.stress_level = max(0.0, min(1.0, body.stress_level))
    if body.safety_score is not None:
        user.safety_score = max(0, min(100, body.safety_score))
    if body.financial_health_score is not None:
        user.financial_health_score = max(0, min(100, body.financial_health_score))
    if body.scenarios_completed is not None:
        user.scenarios_completed = body.scenarios_completed
    if body.current_streak is not None:
        user.current_streak = body.current_streak
        if body.current_streak > user.longest_streak:
            user.longest_streak = body.current_streak

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = result.scalars().all()
    return [AchievementResponse.model_validate(a) for a in achievements]
