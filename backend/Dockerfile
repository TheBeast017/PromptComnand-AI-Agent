FROM python:3.11-slim

LABEL maintainer="TheBeast017"
LABEL description="Prompt Engineer API — generates structured prompts via Claude"

WORKDIR /app

# Install dependencies first to maximize Docker layer cache reuse.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# Use 2 workers in production; tune WEB_CONCURRENCY via Railway env if needed.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--no-access-log"]
