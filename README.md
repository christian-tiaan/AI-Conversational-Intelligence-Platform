# Synvoraith AI — Conversational Intelligence Platform

An extensible SaaS foundation for conversational AI, content generation, document-grounded answers, and live customer support.

## Architecture

- **API:** FastAPI / Python
- **Model integration:** configurable OpenAI-compatible chat endpoint (no provider lock-in)
- **Knowledge retrieval:** planned PostgreSQL + pgvector integration
- **Frontend:** planned React / Next.js client
- **Deployment:** Docker; Render blueprint included as a starter
- **Secrets:** environment variables only

## Quick start

1. Copy `.env.example` to `.env`.
2. Set `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` for your chosen model provider.
3. Run:

```bash
docker compose up --build
```

4. Open http://localhost:8000/docs for the API.

## API endpoints

- `GET /health` — health check
- `GET /api/v1/status` — service status
- `POST /api/v1/chat` — chat completion through the configured model endpoint

## Deployment

The included `Dockerfile` and `render.yaml` provide a starter deployment configuration. Add secrets in the hosting provider's environment settings. Do not commit API keys, user data, datasets containing personal information, or model weights.

## Roadmap

1. Authentication and tenant isolation
2. Streaming chat and conversation persistence
3. Retrieval-augmented generation (RAG) with document ingestion
4. Content studio
5. Live support inbox and human handoff
6. Admin analytics, usage limits, billing, and monitoring
7. Model evaluation and optional LoRA fine-tuning pipeline

This repository is the application source of truth. Large model checkpoints and private datasets should be stored in secured artifact/object storage with versioned references in the project.
