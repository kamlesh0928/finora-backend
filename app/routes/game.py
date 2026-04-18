"""Game progress routes — submit decisions, view progress, reset."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.game_progress import GameProgress
from ..models.achievement import UserAchievement
from ..schemas.schemas import (
    AwardAchievementRequest,
    AchievementResponse,
    GameProgressResponse,
    MessageResponse,
    SubmitDecisionRequest,
)

router = APIRouter(prefix="/game", tags=["Game"])


@router.get("/progress/{module}", response_model=list[GameProgressResponse])
async def get_progress(
    module: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all completed decisions for a specific module."""
    result = await db.execute(
        select(GameProgress)
        .where(GameProgress.user_id == user.id, GameProgress.module == module)
        .order_by(GameProgress.completed_at.asc())
    )
    items = result.scalars().all()
    return [GameProgressResponse.model_validate(i) for i in items]


@router.get("/progress", response_model=list[GameProgressResponse])
async def get_all_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all completed decisions across all modules."""
    result = await db.execute(
        select(GameProgress)
        .where(GameProgress.user_id == user.id)
        .order_by(GameProgress.completed_at.desc())
    )
    items = result.scalars().all()
    return [GameProgressResponse.model_validate(i) for i in items]


@router.post("/decision", response_model=GameProgressResponse, status_code=201)
async def submit_decision(
    body: SubmitDecisionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a player decision and update user game state."""
    progress = GameProgress(
        user_id=user.id,
        module=body.module,
        scenario_id=body.scenario_id,
        decision_index=body.decision_index,
        decision_title=body.decision_title,
        savings_impact=body.savings_impact,
        stress_impact=body.stress_impact,
        wallet_impact=body.wallet_impact,
        notes=body.notes,
    )
    db.add(progress)

    # Update user game state
    if body.wallet_impact > 0:
        user.wallet_balance += body.wallet_impact
        user.total_earned += body.wallet_impact
    elif body.wallet_impact < 0:
        user.wallet_balance = max(0, user.wallet_balance + body.wallet_impact)
        user.total_spent += abs(body.wallet_impact)

    user.stress_level = max(0.0, min(1.0, user.stress_level + body.stress_impact))
    user.scenarios_completed += 1

    # Recalculate financial health score
    health = 50
    if user.wallet_balance >= 10000:
        health += 15
    elif user.wallet_balance >= 5000:
        health += 10
    if user.emergency_fund >= 50000:
        health += 15
    elif user.emergency_fund >= 10000:
        health += 10
    if user.stress_level < 0.3:
        health += 10
    elif user.stress_level > 0.7:
        health -= 10
    if user.safety_score >= 80:
        health += 10
    user.financial_health_score = max(0, min(100, health))

    await db.commit()
    await db.refresh(progress)

    return GameProgressResponse.model_validate(progress)


@router.post("/reset/{module}", response_model=MessageResponse)
async def reset_module(
    module: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset all progress for a specific module."""
    await db.execute(
        delete(GameProgress).where(
            GameProgress.user_id == user.id,
            GameProgress.module == module,
        )
    )

    # Reset relevant user state
    if module == "all":
        user.wallet_balance = 5000.0
        user.emergency_fund = 0.0
        user.stress_level = 0.20
        user.safety_score = 50
        user.financial_health_score = 50
        user.scenarios_completed = 0
        user.total_earned = 0.0
        user.total_spent = 0.0

    await db.commit()
    return MessageResponse(message=f"Progress for '{module}' has been reset.")


@router.post("/achievement", response_model=AchievementResponse, status_code=201)
async def award_achievement(
    body: AwardAchievementRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Award a badge to the user. Idempotent — won't duplicate."""
    # Check if already earned
    result = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id,
            UserAchievement.badge_id == body.badge_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return AchievementResponse.model_validate(existing)

    achievement = UserAchievement(
        user_id=user.id,
        badge_id=body.badge_id,
        badge_name=body.badge_name,
        badge_description=body.badge_description,
        badge_icon=body.badge_icon,
    )
    db.add(achievement)
    await db.commit()
    await db.refresh(achievement)

    return AchievementResponse.model_validate(achievement)
