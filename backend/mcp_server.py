import os
import json
import httpx
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

mcp = FastMCP("GitHubDevCard")

# Configure Directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
CARDS_DIR = STATIC_DIR / "cards"
STATS_FILE = STATIC_DIR / "stats.json"

CARDS_DIR.mkdir(parents=True, exist_ok=True)
if not STATS_FILE.exists():
    STATS_FILE.write_text(json.dumps({}))

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch and aggregate GitHub profile data."""
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient(headers=headers) as client:
        # User details
        user_res = await client.get(f"https://api.github.com/users/{username}")
        if user_res.status_code != 200:
            return {"error": "User not found"}
        user = user_res.json()

        # Repos
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100")
        repos = repos_res.json() if repos_res.status_code == 200 else []

    # Aggregate languages
    languages = {}
    total_repos_with_lang = 0
    days_of_week = []
    total_stars = 0
    
    for r in repos:
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
            total_repos_with_lang += 1
            
        total_stars += r.get("stargazers_count", 0)
        
        updated_at = r.get("updated_at")
        if updated_at:
            dt = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
            days_of_week.append(dt.strftime("%A"))

    lang_stats = {l: round((c / total_repos_with_lang) * 100, 1) for l, c in languages.items()} if total_repos_with_lang else {}
    top_langs = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:5]

    most_active_day = max(set(days_of_week), key=days_of_week.count) if days_of_week else "Unknown"
    
    # Top 6 repos
    top_repos = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:6]
    top_repos_data = [{
        "name": r["name"],
        "stars": r["stargazers_count"],
        "language": r["language"],
        "description": r["description"]
    } for r in top_repos]
    
    # Activity score calculation
    followers_count = user.get("followers", 0)
    public_repos_count = user.get("public_repos", 0)
    activity_score = min(100, (public_repos_count * 3) + (followers_count * 0.5) + (total_stars * 2))
    
    # Card theme determination
    top_lang = top_langs[0][0].lower() if top_langs else ""
    if top_lang in ["python", "jupyter notebook"]:
        card_theme = "researcher"
    elif top_lang in ["javascript", "typescript"]:
        card_theme = "builder"
    elif top_lang in ["c", "c++", "rust", "go"]:
        card_theme = "hacker"
    elif top_lang in ["css", "html", "figma"]:
        card_theme = "designer"
    else:
        card_theme = "open-source-hero"

    # Calculate Real Streak from HTML
    current_streak = 0
    try:
        contrib_url = f"https://github.com/users/{username}/contributions"
        # Create a new client or just reuse the existing httpx without auth for the public HTML
        async with httpx.AsyncClient() as c:
            contrib_res = await c.get(contrib_url)
            if contrib_res.status_code == 200:
                import re
                pattern = r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"'
                matches = re.findall(pattern, contrib_res.text)
                matches.sort(key=lambda x: x[0], reverse=True)
                
                started = False
                for date_str, level in matches:
                    if int(level) > 0:
                        current_streak += 1
                        started = True
                    else:
                        if not started:
                            continue
                        break
    except Exception:
        pass

    return {
        "name": user.get("name") or username,
        "username": username,
        "avatar_url": user.get("avatar_url"),
        "bio": user.get("bio"),
        "location": user.get("location"),
        "public_repos": user.get("public_repos"),
        "followers": user.get("followers"),
        "following": user.get("following"),
        "account_created_year": user.get("created_at")[:4] if user.get("created_at") else "Unknown",
        "top_repos": top_repos_data,
        "languages": dict(top_langs),
        "most_active_day": most_active_day,
        "contribution_streak": f"{current_streak} days",
        "activity_score": activity_score,
        "card_theme": card_theme
    }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data to generate developer insights."""
    
    # 1. Top Skills
    langs = list(github_data.get("languages", {}).keys())
    top_skills = langs[:3] if langs else ["Git", "Debugging", "Learning"]
    
    # 2. Career Suggestion
    theme = github_data.get("card_theme", "builder")
    suggestions = {
        "hacker": "Systems Engineer",
        "builder": "Full Stack Developer",
        "researcher": "Data Scientist",
        "designer": "Frontend Developer",
        "open-source-hero": "Open Source Maintainer"
    }
    career = suggestions.get(theme, "Software Engineer")
    
    # 3. Developer Vibe
    vibes = {
        "hacker": "Living in the terminal, optimizing the unoptimized.",
        "builder": "Shipping features and stacking blocks.",
        "researcher": "Finding patterns in the noise.",
        "designer": "Making the web a more beautiful place.",
        "open-source-hero": "Building in public, for the public."
    }
    vibe = vibes.get(theme, "Code explorer navigating the digital frontier.")
    if top_skills:
        vibe = f"{top_skills[0]} enthusiast building the modern web."
    
    # 4. Profile Tips
    tips = []
    repos = github_data.get("public_repos", 0) or 0
    followers = github_data.get("followers", 0) or 0
    
    if repos < 5:
        tips.append("Create more public repositories to showcase your skills.")
    else:
        tips.append("Pin your best projects to your profile overview.")
        
    if followers < 10:
        tips.append("Engage with the developer community to grow your network.")
    else:
        tips.append("Consider writing technical articles about your top projects.")
        
    if len(langs) < 3:
        tips.append("Explore new programming languages to broaden your stack.")
    else:
        tips.append(f"Contribute to open source {top_skills[0]} projects.")
        
    # 5. Fun Fact
    fun_fact = f"Most productive on {github_data.get('most_active_day', 'weekdays')}s."

    return {
        "developer_vibe": vibe,
        "top_skills": top_skills,
        "fun_fact": fun_fact,
        "career_suggestion": career,
        "profile_tips": tips[:3]
    }

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained, professional HTML dev card."""
    theme = github_data.get("card_theme", "builder")
    themes = {
        "hacker": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        "builder": "linear-gradient(135deg, #1e3c72, #2a5298)",
        "researcher": "linear-gradient(135deg, #6a11cb, #2575fc)",
        "designer": "linear-gradient(135deg, #ff9a9e, #fad0c4)",
        "open-source-hero": "linear-gradient(135deg, #f83600, #f9d423)"
    }
    bg_color = themes.get(theme, themes["builder"])
    accent_color = "#238636" if theme == "hacker" else "#58a6ff"
    
    # Progress ring calculation
    score = github_data.get("activity_score", 50)
    offset = 440 - (440 * score / 100)

    # Language chart HTML
    lang_html = ""
    for lang, pct in github_data.get("languages", {}).items():
        lang_html += f"""
        <div class="lang-row">
            <span class="lang-name">{lang}</span>
            <div class="bar-bg"><div class="bar-fill" style="width: {pct}%; background: {accent_color};"></div></div>
            <span class="lang-pct">{pct}%</span>
        </div>
        """

    # Repos HTML
    repos_html = ""
    for repo in github_data.get("top_repos", [])[:3]:
        repos_html += f"""
        <div class="repo-card">
            <div class="repo-top"><strong>{repo['name']}</strong> <span>⭐ {repo['stars']}</span></div>
            <div class="repo-lang">{repo['language'] or 'Misc'}</div>
        </div>
        """

    # Tips HTML
    tips_html = "".join([f"<li>{tip}</li>" for tip in analysis.get("profile_tips", [])])
    skills_html = "".join([f'<span class="badge">{skill}</span>' for skill in analysis.get("top_skills", [])])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --accent: {accent_color}; }}
            body {{ font-family: 'Inter', sans-serif; background: transparent; margin: 0; display: flex; justify-content: center; }}
            .card {{ 
                width: 450px; background: {bg_color}; color: white; padding: 30px; border-radius: 20px; 
                box-shadow: 0 20px 50px rgba(0,0,0,0.3); position: relative; overflow: hidden;
            }}
            .header {{ display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }}
            .avatar {{ width: 80px; height: 80px; border-radius: 50%; border: 3px solid white; }}
            .vibe {{ font-style: italic; color: #cbd5e0; margin-bottom: 15px; font-size: 0.9rem; }}
            .score-container {{ position: absolute; top: 30px; right: 30px; text-align: center; }}
            .score-ring {{ width: 80px; height: 80px; transform: rotate(-90deg); }}
            .score-ring circle {{ fill: none; stroke-width: 8; stroke-linecap: round; }}
            .score-ring .bg {{ stroke: rgba(255,255,255,0.1); }}
            .score-ring .progress {{ stroke: var(--accent); stroke-dasharray: 440; stroke-dashoffset: {offset}; transition: stroke-dashoffset 1s ease-out; }}
            .score-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: 700; font-size: 1.2rem; }}
            .stats {{ display: flex; justify-content: space-around; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; margin-bottom: 20px; }}
            .stat-item {{ text-align: center; }}
            .stat-val {{ display: block; font-weight: 700; font-size: 1.1rem; }}
            .stat-lbl {{ font-size: 0.7rem; color: #a0aec0; }}
            .lang-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
            .lang-name {{ width: 80px; font-size: 0.8rem; }}
            .bar-bg {{ flex-grow: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }}
            .bar-fill {{ height: 100%; transition: width 1s ease-out; }}
            .lang-pct {{ width: 40px; font-size: 0.7rem; text-align: right; }}
            .career-box {{ background: var(--accent); color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 600; margin: 20px 0; }}
            .badge {{ background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; margin-right: 5px; }}
            .repos {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .repo-card {{ background: rgba(255,255,255,0.05); padding: 8px; border-radius: 8px; font-size: 0.7rem; border: 1px solid rgba(255,255,255,0.1); }}
            .tips-section {{ font-size: 0.8rem; background: rgba(0,0,0,0.1); padding: 10px; border-radius: 10px; }}
            .tips-section ul {{ padding-left: 20px; margin: 5px 0; }}
            .share-btn {{ 
                display: block; width: 100%; padding: 12px; margin-top: 20px; background: #0077b5; 
                color: white; text-decoration: none; text-align: center; border-radius: 10px; font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <img src="{github_data['avatar_url']}" class="avatar">
                <div>
                    <h2 style="margin:0;">{github_data['name']}</h2>
                    <p style="margin:0; color: #a0aec0;">@{github_data['username']}</p>
                </div>
            </div>
            
            <div class="score-container">
                <svg class="score-ring" viewBox="0 0 160 160">
                    <circle class="bg" cx="80" cy="80" r="70"/>
                    <circle class="progress" cx="80" cy="80" r="70"/>
                </svg>
                <div class="score-text">{score}</div>
                <div style="font-size: 0.6rem; color: #a0aec0;">ACTIVITY</div>
            </div>

            <p class="vibe">"{analysis.get('developer_vibe', '')}"</p>
            
            <div class="stats">
                <div class="stat-item"><span class="stat-val">{github_data['public_repos']}</span><span class="stat-lbl">REPOS</span></div>
                <div class="stat-item"><span class="stat-val">{github_data['followers']}</span><span class="stat-lbl">FOLLOWERS</span></div>
                <div class="stat-item"><span class="stat-val">{github_data['contribution_streak']}</span><span class="stat-lbl">STREAK</span></div>
            </div>

            <div class="languages">
                <h4 style="margin-bottom: 10px; font-size: 0.9rem;">Top Languages</h4>
                {lang_html}
            </div>

            <div class="career-box">🚀 {analysis.get('career_suggestion', '')}</div>

            <div style="margin-bottom: 20px;">{skills_html}</div>

            <div class="repos">{repos_html}</div>

            <div class="tips-section">
                <strong>Profile Tips:</strong>
                <ul>{tips_html}</ul>
            </div>

            <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github-dev-card.app/{username}" class="share-btn">Share on LinkedIn</a>
        </div>
    </body>
    </html>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save generated HTML card to disk."""
    file_path = CARDS_DIR / f"{username}.html"
    file_path.write_text(html, encoding="utf-8")
    
    # Update stats
    stats = json.loads(STATS_FILE.read_text())
    stats[username] = stats.get(username, 0) + 1
    STATS_FILE.write_text(json.dumps(stats))
    
    return f"/static/cards/{username}.html"

@mcp.tool()
async def get_card_stats(username: str) -> dict:
    """Retrieve generation stats for a user."""
    stats = json.loads(STATS_FILE.read_text())
    return {
        "username": username,
        "generation_count": stats.get(username, 0)
    }

if __name__ == "__main__":
    mcp.run()
