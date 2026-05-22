# DevCard

GitHub profile analyzer and developer card generator built with Google ADK, MCP workflows, Gemini, and FastAPI.

DevCard analyzes public GitHub profiles and generates personalized developer cards, profile insights, activity scores, role suggestions, and GitHub README content automatically.

## Live Demo

https://devdna-app-181500746472.us-central1.run.app/

---

## Features

### Developer Card Generation
Generate shareable developer cards from any public GitHub profile.

- GitHub profile analysis
- Activity score calculation
- Top languages and stack detection
- Career role suggestions
- Shareable developer card UI

### Private Dashboard

Detailed insights only visible to the user:

- Profile improvement suggestions
- Repository insights
- GitHub activity analysis

### GitHub Profile Comparison

Compare two GitHub profiles side by side:

- Repositories
- Followers
- Stars
- Activity score
- Overall profile comparison

### README Generator

Automatically generate GitHub profile README files based on:

- Tech stack
- Repositories
- Activity patterns
- Developer profile information

---

## Tech Stack

**Frontend**
- HTML
- CSS
- JavaScript

**Backend**
- FastAPI
- Python

**AI & Agent Workflow**
- Google ADK
- MCP
- Gemini API
- Vertex AI Memory Bank

**Cloud & Deployment**
- Docker
- Google Cloud Run
- AntiGravity


## Workflow Architecture


User Input
      ↓
FastAPI Backend
      ↓
ADK Agent Orchestration
      ↓
MCP Tool Calling
      ↓
GitHub API
      ↓
Gemini Analysis
      ↓
Profile Insights + Activity Score
      ↓
Dev Card / Dashboard / README Output
