"""Fraud detection routes — AI-powered SMS analysis."""

from fastapi import APIRouter, HTTPException

from ..schemas.schemas import FraudAnalyzeRequest, FraudAnalyzeResponse
from ..services.fraud_detection import analyze_sms

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])

# ── Static live-feed data (curated trending scams) ───────────────────────────

LIVE_FEED = [
    {
        "id": "feed_1",
        "type": "UPI Fraud",
        "title": "Fake UPI Collect Requests",
        "description": "Scammers send UPI collect requests pretending to be refunds. Never accept collect requests from unknown sources.",
        "severity": "high",
        "date": "2026-04-10",
    },
    {
        "id": "feed_2",
        "type": "KYC Scam",
        "title": "Fake Bank KYC Messages",
        "description": "Messages claiming your bank account will be blocked unless you update KYC via a link. Banks never send such SMS.",
        "severity": "high",
        "date": "2026-04-08",
    },
    {
        "id": "feed_3",
        "type": "Job Scam",
        "title": "Work From Home Fraud",
        "description": "Fake job offers promising ₹30,000-50,000/month for data entry. They ask for registration fees upfront.",
        "severity": "medium",
        "date": "2026-04-06",
    },
    {
        "id": "feed_4",
        "type": "Investment Scam",
        "title": "Cryptocurrency Ponzi Schemes",
        "description": "Telegram groups promising guaranteed 200% returns on crypto investments. No investment guarantees returns.",
        "severity": "high",
        "date": "2026-04-05",
    },
    {
        "id": "feed_5",
        "type": "Phishing",
        "title": "Fake Delivery OTP Scam",
        "description": "Callers pretending to be delivery agents asking you to share OTP for 'address verification'. Never share OTP.",
        "severity": "high",
        "date": "2026-04-03",
    },
    {
        "id": "feed_6",
        "type": "Lottery Scam",
        "title": "WhatsApp Lottery Winners",
        "description": "Messages on WhatsApp claiming you won a lottery. They ask for processing fees. No real lottery contacts via WhatsApp.",
        "severity": "medium",
        "date": "2026-04-01",
    },
    {
        "id": "feed_7",
        "type": "SIM Swap",
        "title": "SIM Swap Fraud Alert",
        "description": "Fraudsters clone your SIM to intercept OTPs. If your phone suddenly loses signal, contact your operator immediately.",
        "severity": "critical",
        "date": "2026-03-28",
    },
    {
        "id": "feed_8",
        "type": "E-commerce",
        "title": "Fake E-commerce Websites",
        "description": "Websites with massive discounts (90% off) on branded goods. Always verify the URL and check for HTTPS.",
        "severity": "medium",
        "date": "2026-03-25",
    },
]

# ── Static micro-challenges ──────────────────────────────────────────────────

MICRO_CHALLENGES = [
    {
        "id": "mc_1",
        "type": "spot_fake_sms",
        "title": "Spot the Fake Bank Message",
        "question": "Which of these SMS messages is a scam?",
        "options": [
            {"id": "a", "text": "Dear Customer, your a/c XX1234 credited with Rs.5,000. Ref: NEFT/UTR123456. -SBI", "is_scam": False},
            {"id": "b", "text": "URGENT: Your SBI account is blocked! Click http://sbi-verify.xyz to reactivate immediately. -SBI", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "Real bank SMS never contains links asking you to click. The domain 'sbi-verify.xyz' is not an official SBI domain.",
        "points": 10,
    },
    {
        "id": "mc_2",
        "type": "unsafe_link",
        "title": "Which Link is Unsafe?",
        "question": "Which of these URLs would you NOT click?",
        "options": [
            {"id": "a", "text": "https://www.onlinesbi.sbi/", "is_scam": False},
            {"id": "b", "text": "https://sbi-login-secure.xyz/verify", "is_scam": True},
            {"id": "c", "text": "https://www.sbi.co.in/web/personal-banking", "is_scam": False},
            {"id": "d", "text": "https://sbi-kyc-update.herokuapp.com", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "The domain 'sbi-login-secure.xyz' uses a suspicious TLD (.xyz) and is not an official SBI website. Official SBI domains end in .sbi or .co.in.",
        "points": 10,
    },
    {
        "id": "mc_3",
        "type": "fake_caller",
        "title": "Which Caller is Lying?",
        "question": "You receive two calls. Which caller is a scammer?",
        "options": [
            {"id": "a", "text": "Caller A: 'I'm from HDFC Bank branch Andheri. Please visit our branch with your ID for KYC update by April 30th.'", "is_scam": False},
            {"id": "b", "text": "Caller B: 'I'm from HDFC head office. Your account will be frozen in 2 hours. Share your OTP now to prevent this.'", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "Banks never ask for OTP over phone calls. The urgency ('2 hours') is a pressure tactic. Real banks ask you to visit a branch.",
        "points": 10,
    },
    {
        "id": "mc_4",
        "type": "spot_fake_sms",
        "title": "Spot the Fake PM-KISAN Message",
        "question": "Which message is a scam?",
        "options": [
            {"id": "a", "text": "PM-KISAN: Rs.6000 credited to your a/c linked with Aadhaar XXXX1234. Check at pmkisan.gov.in", "is_scam": False},
            {"id": "b", "text": "PM-KISAN: Your ₹6,000 payment is pending. Verify Aadhaar at http://pmkisan-verify.in/claim to receive.", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "PM-KISAN never asks you to click links to receive money. The official website is pmkisan.gov.in (notice .gov.in). Scam uses a fake domain.",
        "points": 10,
    },
    {
        "id": "mc_5",
        "type": "unsafe_link",
        "title": "Spot the Suspicious App",
        "question": "You're downloading a banking app. Which one is suspicious?",
        "options": [
            {"id": "a", "text": "SBI YONO - Publisher: State Bank of India | Downloads: 10Cr+ | Rating: 4.2", "is_scam": False},
            {"id": "b", "text": "SBI YONO Lite Pro - Publisher: SBI Finance Ltd | Downloads: 5,000 | Rating: 4.8", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "The fake app has very few downloads, a suspicious publisher name, and an unusually high rating. Always check the publisher name and download count.",
        "points": 10,
    },
    {
        "id": "mc_6",
        "type": "fake_caller",
        "title": "Identify the Scam Call",
        "question": "Which call scenario is a scam?",
        "options": [
            {"id": "a", "text": "'Hello, this is Amazon delivery. Your package #AZ1234 is at the gate. Please come to collect.'", "is_scam": False},
            {"id": "b", "text": "'Hello, this is Amazon. Your order is stuck in customs. Pay ₹499 clearance fee via UPI to 9876543210 to release it.'", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "Amazon never asks for payments via personal UPI numbers. Any extra charges would be handled through the official Amazon app/website.",
        "points": 10,
    },
    {
        "id": "mc_7",
        "type": "spot_fake_sms",
        "title": "Spot the Lottery Scam",
        "question": "Which message is a scam?",
        "options": [
            {"id": "a", "text": "Congratulations! You won ₹25,00,000 in Jio Lucky Draw! Claim now: http://jio-prize.com Pay ₹999 processing fee.", "is_scam": True},
            {"id": "b", "text": "Your Jio recharge of ₹399 is successful. Validity: 28 days. Data: 2GB/day. Thank you! -Jio", "is_scam": False},
        ],
        "correct_answer": "a",
        "explanation": "No company asks winners to pay a 'processing fee'. This is a classic advance-fee lottery scam. Real prizes never require payment.",
        "points": 10,
    },
    {
        "id": "mc_8",
        "type": "unsafe_link",
        "title": "QR Code Safety",
        "question": "Someone sends you this QR code scenario. Which is safe?",
        "options": [
            {"id": "a", "text": "A shopkeeper shows QR at their counter to receive your payment of ₹200 for groceries.", "is_scam": False},
            {"id": "b", "text": "A stranger at an ATM asks you to scan their QR code to 'receive' ₹500 they owe you.", "is_scam": True},
        ],
        "correct_answer": "b",
        "explanation": "Scanning QR codes is for PAYING, not receiving money. If someone asks you to scan a QR to 'receive' money, it's a scam — you'll actually send money.",
        "points": 10,
    },
]


@router.post("/analyze-sms", response_model=FraudAnalyzeResponse)
async def analyze_sms_endpoint(body: FraudAnalyzeRequest):
    """Analyze an SMS message for fraud using Gemini AI."""
    try:
        result = await analyze_sms(body.sms_text)
        return FraudAnalyzeResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI analysis temporarily unavailable: {str(e)}",
        )


@router.get("/live-feed")
async def get_live_feed():
    """Get trending fraud patterns and scam alerts."""
    return LIVE_FEED


@router.get("/micro-challenges")
async def get_micro_challenges():
    """Get all available micro-challenges."""
    return MICRO_CHALLENGES


@router.post("/micro-challenge/{challenge_id}/submit")
async def submit_micro_challenge(challenge_id: str, answer: str):
    """Submit answer for a micro-challenge."""
    challenge = next((c for c in MICRO_CHALLENGES if c["id"] == challenge_id), None)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    is_correct = answer == challenge["correct_answer"]
    return {
        "correct": is_correct,
        "correct_answer": challenge["correct_answer"],
        "explanation": challenge["explanation"],
        "points_earned": challenge["points"] if is_correct else 0,
    }
