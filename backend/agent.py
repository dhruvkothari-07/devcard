import os
from dotenv import load_dotenv

from google.adk import Agent

from tools import (
    scrape_github,
    analyze_profile,
    generate_card_html,
    save_card,
    get_card_stats,
)

load_dotenv()

SYSTEM_INSTRUCTION = """
You are a professional GitHub profile analyst and dev card generator. When a user gives you a GitHub username, you ALWAYS follow this exact sequence:
1. Call scrape_github to get the profile data
2. Call analyze_profile with the scraped data to get AI analysis including activity_score, career_suggestion and profile_tips
3. Call generate_card_html with username, github_data and analysis to build the card
4. Call save_card to save and get the URL
5. Call get_card_stats to get view count

Never skip any step. Never change the order. Be enthusiastic about developers work. 
If the profile is private or does not exist (e.g., scrape_github returns an error), say so clearly and suggest checking the username spelling.
"""


def create_github_card_agent():
    """Create the GitHub Card Generator agent using plain function tools."""
    return Agent(
        name="github_card_agent",
        model="gemini-2.0-flash",
        description="An agent that generates professional GitHub developer cards.",
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            scrape_github,
            analyze_profile,
            generate_card_html,
            save_card,
            get_card_stats,
        ],
    )
