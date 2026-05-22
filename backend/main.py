import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from tools import (
    scrape_github,
    analyze_profile,
    generate_card_html,
    save_card,
    get_card_stats,
)

app = FastAPI(title="GitHub Dev Card API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
CARDS_DIR = STATIC_DIR / "cards"
FRONTEND_DIR = BASE_DIR / "frontend"
CARDS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for direct access
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Mount frontend assets (CSS, JS)
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


class GenerateRequest(BaseModel):
    username: str


@app.get("/")
async def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate_card_endpoint(request: GenerateRequest):
    username = request.username

    try:
        # Step 1: Scrape GitHub profile
        github_data = await scrape_github(username)
        if "error" in github_data:
            raise HTTPException(status_code=404, detail=github_data["error"])

        # Step 2: Analyze profile with Gemini
        analysis = await analyze_profile(github_data)

        # Step 3: Generate HTML card
        html = await generate_card_html(username, github_data, analysis)

        # Step 4: Save the card
        card_url = await save_card(username, html)

        # Step 5: Get stats
        stats = await get_card_stats(username)

        return {
            "card_url": card_url,
            "activity_score": github_data.get("activity_score", 0),
            "career_suggestion": analysis.get("career_suggestion", ""),
            "developer_vibe": analysis.get("developer_vibe", ""),
            "top_skills": analysis.get("top_skills", []),
            "fun_fact": analysis.get("fun_fact", ""),
            "profile_tips": analysis.get("profile_tips", []),
            "card_theme": github_data.get("card_theme", "builder"),
            "github_data": github_data,
            "generation_count": stats.get("generation_count", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/card/{username}")
async def get_card(username: str):
    file_path = CARDS_DIR / f"{username}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Card not found")
    return FileResponse(file_path)


@app.get("/stats/{username}")
async def get_stats(username: str):
    stats_file = STATIC_DIR / "stats.json"
    if not stats_file.exists():
        return {"username": username, "generation_count": 0}

    stats = json.loads(stats_file.read_text())
    return {
        "username": username,
        "generation_count": stats.get(username, 0),
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
