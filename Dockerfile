FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend code
COPY frontend/ ./frontend/

# Create static directories
RUN mkdir -p static/cards

# Cloud Run sets PORT env var
ENV PORT=8080

# Run from backend directory
WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
