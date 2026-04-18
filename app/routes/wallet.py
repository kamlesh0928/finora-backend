"""Wallet routes — balance, transactions, credit/debit."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.transaction import Transaction
from ..schemas.schemas import (
    MessageResponse,
    TransactionResponse,
    WalletResponse,
    WalletTransactionRequest,
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance", response_model=WalletResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return WalletResponse(
        balance=user.wallet_balance,
        emergency_fund=user.emergency_fund,
        total_earned=user.total_earned,
        total_spent=user.total_spent,
    )


@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
):
    query = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
    )
    if category:
        query = query.where(Transaction.category == category)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    txns = result.scalars().all()
    return [TransactionResponse.model_validate(t) for t in txns]


@router.post("/credit", response_model=TransactionResponse, status_code=201)
async def credit_wallet(
    body: WalletTransactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add money to wallet (salary, rewards, good decisions)."""
    user.wallet_balance += body.amount
    user.total_earned += body.amount

    txn = Transaction(
        user_id=user.id,
        amount=body.amount,
        tx_type="credit",
        category=body.category,
        description=body.description,
        source_module=body.source_module,
        scenario_id=body.scenario_id,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    return TransactionResponse.model_validate(txn)


@router.post("/debit", response_model=TransactionResponse, status_code=201)
async def debit_wallet(
    body: WalletTransactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deduct money from wallet (scams, expenses, bad decisions)."""
    user.wallet_balance = max(0, user.wallet_balance - body.amount)
    user.total_spent += body.amount

    txn = Transaction(
        user_id=user.id,
        amount=body.amount,
        tx_type="debit",
        category=body.category,
        description=body.description,
        source_module=body.source_module,
        scenario_id=body.scenario_id,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    return TransactionResponse.model_validate(txn)
