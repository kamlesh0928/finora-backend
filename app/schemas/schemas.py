from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Auth

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# User

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: Optional[str] = None
    language: str = "en"
    wallet_balance: float = 5000.0
    emergency_fund: float = 0.0
    financial_health_score: int = 50
    stress_level: float = 0.20
    safety_score: int = 50
    total_earned: float = 0.0
    total_spent: float = 0.0
    scenarios_completed: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    language: Optional[str] = None


class UpdateGameStateRequest(BaseModel):
    wallet_balance: Optional[float] = None
    emergency_fund: Optional[float] = None
    stress_level: Optional[float] = None
    safety_score: Optional[int] = None
    financial_health_score: Optional[int] = None
    scenarios_completed: Optional[int] = None
    current_streak: Optional[int] = None


# Wallet

class WalletTransactionRequest(BaseModel):
    amount: float = Field(..., gt=0)
    category: str  # budgeting, fraud, emergency, scenario, salary, reward
    description: str
    source_module: Optional[str] = None
    scenario_id: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    tx_type: str
    category: str
    description: str
    source_module: Optional[str] = None
    scenario_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    balance: float
    emergency_fund: float
    total_earned: float
    total_spent: float


# Game Progress

class SubmitDecisionRequest(BaseModel):
    module: str  # budgeting, fraud, emergency, scenario
    scenario_id: str
    decision_index: int
    decision_title: str
    savings_impact: float = 0.0
    stress_impact: float = 0.0
    wallet_impact: float = 0.0
    notes: Optional[str] = None


class GameProgressResponse(BaseModel):
    id: str
    module: str
    scenario_id: str
    decision_index: int
    decision_title: str
    savings_impact: float
    stress_impact: float
    wallet_impact: float
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Fraud Detection

class FraudAnalyzeRequest(BaseModel):
    sms_text: str = Field(..., min_length=5, max_length=2000)


class FraudAnalyzeResponse(BaseModel):
    fraud_status: str  # "Fraud" or "Real"
    confidence: str  # "Low", "Medium", "High"
    reason: str
    safety_advice: str
    links_found: list[str] = []
    domains: list[str] = []


# Sync
class SyncPushItem(BaseModel):
    action: str  # "transaction", "game_progress", "achievement", "update_state"
    payload: dict
    timestamp: datetime
    local_id: Optional[str] = None


class SyncPushRequest(BaseModel):
    items: list[SyncPushItem]
    last_sync_at: Optional[datetime] = None


class SyncPullResponse(BaseModel):
    user: UserResponse
    transactions: list[TransactionResponse] = []
    game_progress: list[GameProgressResponse] = []
    achievements: list["AchievementResponse"] = []
    server_time: datetime


# Achievements

class AchievementResponse(BaseModel):
    id: str
    badge_id: str
    badge_name: str
    badge_description: Optional[str] = None
    badge_icon: Optional[str] = None
    earned_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AwardAchievementRequest(BaseModel):
    badge_id: str
    badge_name: str
    badge_description: Optional[str] = None
    badge_icon: Optional[str] = None


# Generic
class MessageResponse(BaseModel):
    message: str
    success: bool = True
