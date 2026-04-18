import os
import re
import time
import asyncio
from typing import Optional
from dotenv import load_dotenv

import tldextract
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Rate limiting implementation (in-memory, per-minute)

_call_timestamps: list[float] = []


def _rate_limit_check():
    """Raise if we've exceeded the per-minute limit for Gemini free tier."""
    now = time.time()
    # Remove timestamps older than 60s
    _call_timestamps[:] = [t for t in _call_timestamps if now - t < 60]
    rate_limit = int(os.getenv("GEMINI_RATE_LIMIT_PER_MINUTE", "10"))
    if len(_call_timestamps) >= rate_limit:
        raise RuntimeError(
            "Gemini API rate limit reached. Please try again in a minute."
        )
    _call_timestamps.append(now)


# Link extraction and analysis helpers

def extract_links(text: str) -> list[str]:
    """Extract all HTTP(S) URLs from the text."""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)


def analyze_links(links: list[str]) -> list[str]:
    """Extract registered domains from URLs."""
    domains = []
    for link in links:
        ext = tldextract.extract(link)
        domain = f"{ext.domain}.{ext.suffix}"
        if domain != ".":
            domains.append(domain)
    return domains


# AI prompt Configuration
_prompt = PromptTemplate.from_template("""
You are an AI assistant specialized in detecting SMS fraud in India.

Analyze the following SMS message and determine if it is:
1. Fraud / Scam
2. Legitimate / Real

Check for:
- Suspicious links or shortened URLs
- Fake bank domains (SBI, HDFC, ICICI, Axis, Kotak, etc.)
- Requests for OTP, password, PIN, Aadhaar, PAN
- Urgent messages creating panic
- Prize or lottery scams
- Account suspension / KYC threats
- Job offer scams
- UPI payment request scams

SMS Message:
{sms}

Links Found:
{links}

Domains Detected:
{domains}

You MUST return the result in EXACTLY this format with these exact headers:

Fraud Status: <Fraud or Real>
Confidence: <Low or Medium or High>
Reason: <clear explanation>
Safety Advice: <actionable advice for the user>
""")

# Chain and Model Initialization

_model: Optional[ChatGoogleGenerativeAI] = None
_parser = StrOutputParser()


def _get_chain():
    global _model
    if _model is None:
        _model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        )
    return _prompt | _model | _parser


# Result parsing and public API

def _parse_result(raw: str) -> dict:
    """Parse the structured Gemini response into a dict."""
    result = {
        "fraud_status": "Unknown",
        "confidence": "Low",
        "reason": "",
        "safety_advice": "",
    }

    lines = raw.strip().split("\n")
    current_key = None

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.lower().startswith("fraud status:"):
            result["fraud_status"] = line_stripped.split(":", 1)[1].strip()
            current_key = None
        elif line_stripped.lower().startswith("confidence:"):
            result["confidence"] = line_stripped.split(":", 1)[1].strip()
            current_key = None
        elif line_stripped.lower().startswith("reason:"):
            result["reason"] = line_stripped.split(":", 1)[1].strip()
            current_key = "reason"
        elif line_stripped.lower().startswith("safety advice:"):
            result["safety_advice"] = line_stripped.split(":", 1)[1].strip()
            current_key = "safety_advice"
        elif current_key and line_stripped:
            result[current_key] += " " + line_stripped

    return result


async def analyze_sms(sms_text: str) -> dict:
    """
    Analyze an SMS message for fraud using Gemini AI.
    Returns dict with fraud_status, confidence, reason, safety_advice, links_found, domains.
    """
    _rate_limit_check()

    links = extract_links(sms_text)
    domains = analyze_links(links)

    chain = _get_chain()

    # Run synchronous LangChain call in a thread
    raw_result = await asyncio.to_thread(
        chain.invoke,
        {"sms": sms_text, "links": links, "domains": domains},
    )

    parsed = _parse_result(raw_result)
    parsed["links_found"] = links
    parsed["domains"] = domains

    return parsed
