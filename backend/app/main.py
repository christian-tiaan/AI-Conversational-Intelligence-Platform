from __future__ import annotations

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
    ai_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/v1/status")
async def status() -> dict[str, str | bool]:
    return {
        "service": settings.app_name,
        "model_configured": bool(settings.ai_base_url and settings.ai_model),
        "environment": settings.app_env,
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> dict:
    if not settings.ai_base_url or not settings.ai_model:
        raise HTTPException(
            status_code=503,
            detail="AI model is not configured. Set AI_BASE_URL and AI_MODEL.",
        )

    endpoint = settings.ai_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.ai_api_key:
        headers["Authorization"] = f"Bearer {settings.ai_api_key}"

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
        raise HTTPException(status_code=502, detail="The model provider returned an error.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the model provider.") from exc

    choices = result.get("choices") or []
    if not choices:
        raise HTTPException(status_code=502, detail="The model provider returned no choices.")

    return {
        "reply": choices[0].get("message", {}).get("content", ""),
        "model": result.get("model", settings.ai_model),
        "usage": result.get("usage"),
    }
