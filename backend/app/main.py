from __future__ import annotations

import json
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Synvoraith AI Conversational Intelligence"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=800, ge=1, le=4000)


class ContentRequest(BaseModel):
    content_type: str = Field(min_length=2, max_length=80)
    brief: str = Field(min_length=3, max_length=10000)
    tone: str = Field(default="Clear and professional", max_length=100)
    audience: str = Field(default="General audience", max_length=300)


def require_model() -> tuple[str, dict[str, str]]:
    if not settings.ai_base_url or not settings.ai_model:
        raise HTTPException(
            status_code=503,
            detail="AI model is not configured. Set AI_BASE_URL, AI_MODEL and the provider credentials on the backend host.",
        )
    endpoint = settings.ai_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.ai_api_key:
        headers["Authorization"] = f"Bearer {settings.ai_api_key}"
    return endpoint, headers


def extract_text(result: dict) -> str:
    choices = result.get("choices") or []
    if not choices:
        raise HTTPException(status_code=502, detail="The model provider returned no choices.")
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    text = str(content).strip()
    if not text:
        raise HTTPException(status_code=502, detail="The model provider returned an empty response.")
    return text


async def call_model(
    client: httpx.AsyncClient,
    endpoint: str,
    headers: dict[str, str],
    prompt: str,
    *,
    temperature: float = 0.65,
    max_tokens: int = 1800,
) -> str:
    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        response = await client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return extract_text(response.json())
    except httpx.HTTPStatusError as exc:
        provider_message = ""
        try:
            provider_message = str(exc.response.json().get("error", {}).get("message", ""))
        except Exception:
            pass
        detail = "The model provider rejected a content-generation stage."
        if provider_message:
            detail += " " + provider_message[:350]
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the model provider. Check the backend URL and provider availability.") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="The model provider returned an invalid response.") from exc


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/v1/status")
async def status() -> dict[str, str | bool]:
    return {
        "service": settings.app_name,
        "model_configured": bool(settings.ai_base_url and settings.ai_model),
        "environment": settings.app_env,
        "content_pipeline": "four-stage",
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> dict:
    endpoint, headers = require_model()
    payload = {
        "model": settings.ai_model,
        "messages": [message.model_dump() for message in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="The model provider returned an error. Check the configured model and provider settings.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the model provider.") from exc

    return {
        "reply": extract_text(result),
        "model": result.get("model", settings.ai_model),
        "usage": result.get("usage"),
    }


@app.post("/api/v1/content/generate")
async def generate_content(request: ContentRequest) -> dict:
    """Generate content through strategy, architecture, writing and editorial polish."""
    endpoint, headers = require_model()
    content_type = request.content_type.strip()
    brief = request.brief.strip()
    tone = request.tone.strip()
    audience = request.audience.strip() or "General audience"

    short_format = any(term in content_type.lower() for term in (
        "linkedin", "email", "support response", "product description"
    ))
    if short_format:
        length_guidance = (
            "Keep the final piece appropriate to the selected format. For a LinkedIn post, "
            "write about 120-220 words unless the brief clearly requires otherwise. "
            "For an email, include a useful subject line and concise body. Do not turn short-form "
            "content into a long article."
        )
        section_count = 3
    else:
        length_guidance = (
            "Create a substantial, useful draft with a clear introduction, informative sections, "
            "practical examples and a meaningful conclusion. Avoid padding and repetition."
        )
        section_count = 4

    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        strategy = await call_model(
            client, endpoint, headers,
            "You are a senior content strategist. Analyze this brief and return: "
            "1) the strongest audience-relevant angle, 2) the reader's main problem or desire, "
            "3) the key takeaway, 4) three specific points that must be covered. "
            "Be concrete and do not invent facts.\n\n"
            f"Content type: {content_type}\nAudience: {audience}\nTone: {tone}\nBrief: {brief}",
            temperature=0.55, max_tokens=700,
        )

        outline = await call_model(
            client, endpoint, headers,
            "You are an experienced editor. Build a logical, non-repetitive structure for this "
            f"{content_type}. Provide {section_count} concise section headings in a sensible order, "
            "plus a one-sentence purpose for each. Do not include generic filler headings. "
            "Respect the requested content format.\n\n"
            f"Brief: {brief}\nAudience: {audience}\nStrategy: {strategy}",
            temperature=0.45, max_tokens=700,
        )

        draft = await call_model(
            client, endpoint, headers,
            "You are an expert human-sounding writer and subject-matter editor. Write the complete "
            f"{content_type} using the strategy and structure below. Tone: {tone}. Audience: {audience}. "
            f"{length_guidance} Use natural language, varied sentence rhythm, specific useful details, "
            "and clear formatting. Avoid fabricated statistics, citations, customer claims, or facts. "
            "If information is missing, phrase carefully instead of making it up.\n\n"
            f"Original brief:\n{brief}\n\nStrategy:\n{strategy}\n\nStructure:\n{outline}",
            temperature=0.7, max_tokens=2600 if not short_format else 1200,
        )

        final_content = await call_model(
            client, endpoint, headers,
            "Act as a meticulous senior editor. Improve the draft for clarity, flow, accuracy, "
            "readability and usefulness. Remove repetition and generic AI phrasing. Preserve the "
            "meaning and do not add unsupported facts. Return only the finished content, ready to use. "
            "For a blog outline, keep it an outline. For LinkedIn or other short formats, keep it concise.\n\n"
            f"Content type: {content_type}\nTone: {tone}\nAudience: {audience}\nDraft:\n{draft}",
            temperature=0.35, max_tokens=2800 if not short_format else 1400,
        )

    return {
        "content": final_content,
        "strategy": strategy,
        "outline": outline,
        "model": settings.ai_model,
        "pipeline": ["strategy", "outline", "draft", "editorial_polish"],
    }
