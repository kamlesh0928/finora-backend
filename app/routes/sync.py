"""Sync routes — push offline changes, pull latest state."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.transaction import Transaction
from ..models.game_progress import GameProgress
from ..models.achievement import UserAchievement
from ..schemas.schemas import (
    AchievementResponse,
    GameProgressResponse,
    MessageResponse,
    SyncPullResponse,
    SyncPushRequest,
    TransactionResponse,
    UserResponse,
)

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/push", response_model=MessageResponse)
async def push_sync(
    body: SyncPushRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Push offline changes to server.
    Each item in the list is processed in order.
    """
    processed = 0

    for item in body.items:
        try:
            if item.action == "transaction":
                txn = Transaction(
                    user_id=user.id,
                    amount=item.payload.get("amount", 0),
                    tx_type=item.payload.get("tx_type", "debit"),
                    category=item.payload.get("category", "scenario"),
                    description=item.payload.get("description", ""),
                    source_module=item.payload.get("source_module"),
                    scenario_id=item.payload.get("scenario_id"),
                    created_at=item.timestamp,
                    synced=True,
                )
                db.add(txn)

                # Update user balance
                if txn.tx_type == "credit":
                    user.wallet_balance += txn.amount
                    user.total_earned += txn.amount
                else:
                    user.wallet_balance = max(0, user.wallet_balance - txn.amount)
                    user.total_spent += txn.amount

            elif item.action == "game_progress":
                progress = GameProgress(
                    user_id=user.id,
                    module=item.payload.get("module", "scenario"),
                    scenario_id=item.payload.get("scenario_id", ""),
                    decision_index=item.payload.get("decision_index", 0),
                    decision_title=item.payload.get("decision_title", ""),
                    savings_impact=item.payload.get("savings_impact", 0),
                    stress_impact=item.payload.get("stress_impact", 0),
                    wallet_impact=item.payload.get("wallet_impact", 0),
                    notes=item.payload.get("notes"),
                    completed_at=item.timestamp,
                    synced=True,
                )
                db.add(progress)

            elif item.action == "achievement":
                # Check if already earned
                result = await db.execute(
                    select(UserAchievement).where(
                        UserAchievement.user_id == user.id,
                        UserAchievement.badge_id == item.payload.get("badge_id", ""),
                    )
                )
                if not result.scalar_one_or_none():
                    achievement = UserAchievement(
                        user_id=user.id,
                        badge_id=item.payload.get("badge_id", ""),
                        badge_name=item.payload.get("badge_name", ""),
                        badge_description=item.payload.get("badge_description"),
                        badge_icon=item.payload.get("badge_icon"),
                        earned_at=item.timestamp,
                    )
                    db.add(achievement)

            elif item.action == "update_state":
                payload = item.payload
                if "wallet_balance" in payload:
                    user.wallet_balance = max(0, payload["wallet_balance"])
                if "emergency_fund" in payload:
                    user.emergency_fund = max(0, payload["emergency_fund"])
                if "stress_level" in payload:
                    user.stress_level = max(0.0, min(1.0, payload["stress_level"]))
                if "safety_score" in payload:
                    user.safety_score = max(0, min(100, payload["safety_score"]))
                if "scenarios_completed" in payload:
                    user.scenarios_completed = payload["scenarios_completed"]

            processed += 1

        except Exception:
            # Skip individual failures, continue processing rest
            continue

    user.last_sync_at = datetime.now(timezone.utc)
    await db.commit()

    return MessageResponse(message=f"Synced {processed}/{len(body.items)} items successfully")


@router.get("/pull", response_model=SyncPullResponse)
async def pull_sync(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull latest state from server."""
    # Get recent transactions
    txn_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(100)
    )
    transactions = txn_result.scalars().all()

    # Get all game progress
    prog_result = await db.execute(
        select(GameProgress)
        .where(GameProgress.user_id == user.id)
        .order_by(GameProgress.completed_at.desc())
    )
    progress = prog_result.scalars().all()

    # Get achievements
    ach_result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = ach_result.scalars().all()

    user.last_sync_at = datetime.now(timezone.utc)
    await db.commit()

    return SyncPullResponse(
        user=UserResponse.model_validate(user),
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        game_progress=[GameProgressResponse.model_validate(p) for p in progress],
        achievements=[AchievementResponse.model_validate(a) for a in achievements],
        server_time=datetime.now(timezone.utc),
    )
