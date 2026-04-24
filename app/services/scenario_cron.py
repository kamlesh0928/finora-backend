import os
import json
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def generate_weekly_scenarios():
    """Generates weekly financial scenarios using Gemini API."""
    logger.info("Starting weekly scenario generation cron job...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set. Skipping scenario generation.")
        return

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key,
        )

        prompt = PromptTemplate.from_template(
            "Generate 3 realistic financial scenarios for a lower-middle-class individual in India. "
            "For each scenario, provide a title, description, and 2 choices (one good, one bad). "
            "Respond ONLY in valid JSON format as a list of objects with keys: "
            "'title', 'description', 'choices' (list of 'text', 'is_good', 'savings_impact', 'stress_impact')."
        )
        
        chain = prompt | llm
        result = await chain.ainvoke({})
        
        # Parse JSON
        content = result.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        scenarios = json.loads(content.strip())
        
        # Save to a local file for now
        os.makedirs("data", exist_ok=True)
        with open("data/weekly_scenarios.json", "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "scenarios": scenarios
            }, f, indent=2)
            
        logger.info(f"Successfully generated {len(scenarios)} weekly scenarios.")
        
    except Exception as e:
        logger.error(f"Error generating scenarios: {e}")

def start_cron():
    """Starts the scheduler and adds the weekly job."""
    if not scheduler.running:
        # Run every Monday at 00:00
        scheduler.add_job(generate_weekly_scenarios, 'cron', day_of_week='mon', hour=0, minute=0)
        scheduler.start()
        logger.info("Scenario cron job started.")

def stop_cron():
    """Stops the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scenario cron job stopped.")
