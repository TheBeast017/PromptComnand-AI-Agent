"""
Prompt Engineer API — server.py
Converts plain-English commands into structured prompts + system prompts via Groq (Llama).

Changelog:
  v2.3.0 — switched to Groq (free, open-source Llama 3.3 70B); dropped Anthropic dependency.
  v2.2.0 — async client, /api/prompts list endpoint, startup DB indexing, configurable model.
  v2.1.0 — structured logging, CORS from env, retry on LLM errors.
  v2.0.0 — initial async rewrite.
"""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import groq
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo import DESCENDING, IndexModel

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prompt_engineer")


# ---------------------------------------------------------------------------
# Config — all from environment, safe defaults for local dev
# ---------------------------------------------------------------------------
MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME: str = os.environ.get("DB_NAME", "prompt_engineer_db")
GROQ_API_KEY: str | None = os.environ.get("GROQ_API_KEY")
# Free models on Groq: llama-3.3-70b-versatile, llama-3.1-8b-instant,
#                      mixtral-8x7b-32768, gemma2-9b-it
LLM_MODEL: str = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
CORS_ORIGINS: list[str] = os.environ.get("CORS_ORIGINS", "*").split(",")

if not GROQ_API_KEY:
    logger.warning(
        "GROQ_API_KEY is not set — LLM calls will be skipped and the "
        "fallback template will be used instead. Get a free key at https://console.groq.com/"
    )


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]
prompts_collection = db.prompts

# Async Groq client — never blocks the event loop.
ai_client: groq.AsyncGroq | None = (
    groq.AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure indexes exist on startup so queries stay fast as the collection grows.
    await prompts_collection.create_indexes(
        [
            IndexModel([("id", DESCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
        ]
    )
    logger.info("MongoDB indexes ensured.")
    yield
    mongo_client.close()
    logger.info("MongoDB connection closed.")


# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Prompt Engineer API",
    description=(
        "Converts simple natural-language commands into structured, "
        "optimized prompts and system messages using open-source LLMs via Groq."
    ),
    version="2.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class PromptRequest(BaseModel):
    command: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Plain-English description of the task you want to prompt an AI to do.",
        examples=["Write a professional cold email to a potential investor"],
    )


class PromptResponse(BaseModel):
    id: str
    command: str
    structured_prompt: str
    system_prompt: str
    model_used: str
    created_at: str


class PromptListResponse(BaseModel):
    prompts: list[PromptResponse]
    total: int
    skip: int
    limit: int


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_configured: bool
    llm_model: str
    db_connected: bool


# ---------------------------------------------------------------------------
# LLM prompt engineering logic
# ---------------------------------------------------------------------------
_SYSTEM_MESSAGE = """\
You are a senior AI Prompt Engineer with deep expertise in crafting production-grade prompts \
for large language models.

When the user gives you a task description, you produce exactly two things and nothing else:

1. **structured_prompt** — A detailed, markdown-formatted prompt ready to be sent to an AI model.
   It must contain: a clear Context section, a precise Task section, Input/Output format \
specifications, constraints & edge cases, and acceptance criteria. No padding.

2. **system_prompt** — A concise, authoritative system message (3–8 sentences, plain prose, \
no bullet points) that configures an AI's persona and behaviour for this specific task.

Respond ONLY with a valid JSON object in this exact shape — no markdown fences, no extra keys:
{"structured_prompt": "...", "system_prompt": "..."}\
"""


async def _call_groq(command: str) -> tuple[str, str, str]:
    """
    Call Groq to generate structured_prompt + system_prompt.
    Returns (structured_prompt, system_prompt, model_used).
    Raises on any API or parse failure so the caller can fall back.
    """
    assert ai_client is not None

    completion = await ai_client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": _SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": f'Generate prompts for this task:\n\n"{command}"',
            },
        ],
    )

    raw: str = completion.choices[0].message.content.strip()

    # Strip accidental code fences that the model sometimes adds.
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip()

    data: dict = json.loads(raw)

    structured = data["structured_prompt"]
    system = data["system_prompt"]

    if not structured or not system:
        raise ValueError("LLM returned empty prompt fields.")

    return structured, system, completion.model


def _fallback_prompts(command: str) -> tuple[str, str, str]:
    """
    Static template used when the LLM is unavailable.
    Good enough to keep the API functional, but set GROQ_API_KEY for real output.
    """
    structured = f"""\
# Task
{command}

## Context
Provide all relevant background before executing the task.

## Requirements
- Deliver accurate, complete output that directly addresses the task.
- Follow established best practices for the domain.
- Target the appropriate audience and format your response accordingly.

## Output Format
Use clear headings and bullet points where helpful. \
Include concrete examples when they add clarity.

## Acceptance Criteria
- Every requirement is addressed.
- Output is immediately usable without further editing.
- Tone and complexity match the intended audience.
"""

    system = (
        f"You are a highly capable expert assistant. "
        f"Your task is to {command.lower().rstrip('.')}. "
        f"Be thorough, precise, and professional. "
        f"Structure your output clearly and ensure it is production-ready."
    )

    return structured, system, "fallback-template"


async def generate_prompt_pair(command: str) -> tuple[str, str, str]:
    """
    Top-level helper: tries Groq first, falls back to template on any failure.
    Returns (structured_prompt, system_prompt, model_used).
    """
    if ai_client:
        try:
            return await _call_groq(command)
        except (groq.APIError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error("LLM call failed (%s), using fallback template.", exc)

    return _fallback_prompts(command)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["General"], include_in_schema=False)
async def root():
    return {
        "message": "Prompt Engineer API",
        "version": "2.3.0",
        "docs": "/docs",
    }


@app.post(
    "/api/generate-prompt",
    response_model=PromptResponse,
    summary="Generate a structured prompt from a plain-English command",
    tags=["Prompts"],
)
async def generate_prompt(request: PromptRequest):
    command = request.command.strip()
    logger.info("Generating prompt — command=%r model=%s", command, LLM_MODEL)

    structured_prompt, system_prompt, model_used = await generate_prompt_pair(command)

    prompt_id = str(uuid.uuid4())
    record = {
        "id": prompt_id,
        "command": command,
        "structured_prompt": structured_prompt,
        "system_prompt": system_prompt,
        "model_used": model_used,
        "created_at": datetime.utcnow().isoformat(),
    }

    await prompts_collection.insert_one(record)
    record.pop("_id", None)

    logger.info("Saved prompt id=%s model=%s", prompt_id, model_used)
    return PromptResponse(**record)


@app.get(
    "/api/prompts",
    response_model=PromptListResponse,
    summary="List previously generated prompts (newest first)",
    tags=["Prompts"],
)
async def list_prompts(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    cursor = (
        prompts_collection.find()
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    results: list[PromptResponse] = []
    async for doc in cursor:
        doc.pop("_id", None)
        doc.setdefault("model_used", "unknown")  # back-compat for old records
        results.append(PromptResponse(**doc))

    total = await prompts_collection.count_documents({})
    return PromptListResponse(prompts=results, total=total, skip=skip, limit=limit)


@app.get(
    "/api/prompts/{prompt_id}",
    response_model=PromptResponse,
    summary="Fetch a single prompt by ID",
    tags=["Prompts"],
)
async def get_prompt(prompt_id: str):
    record = await prompts_collection.find_one({"id": prompt_id})
    if not record:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")
    record.pop("_id", None)
    record.setdefault("model_used", "unknown")
    return PromptResponse(**record)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Service health check",
    tags=["General"],
)
async def health_check():
    db_ok = False
    try:
        await mongo_client.admin.command("ping")
        db_ok = True
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="2.3.0",
        llm_configured=bool(GROQ_API_KEY),
        llm_model=LLM_MODEL,
        db_connected=db_ok,
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=False)
