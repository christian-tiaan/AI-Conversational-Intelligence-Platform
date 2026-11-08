# Synvoraith AI — Conversational Intelligence Platform

A SaaS starter for conversational AI, business content generation, document-grounded answers, and live customer support.

## Current project status

**Implemented**
- Responsive dark SaaS workspace frontend in `frontend/index.html`
- AI chat UI connected to the backend `POST /api/v1/chat`
- Content Studio using the same model API with writing instructions
- Browser-side backend URL configuration and health diagnostics
- FastAPI model gateway with configurable OpenAI-compatible provider
- Docker and Render starter configuration
- GitHub Actions workflow for deploying the static frontend to GitHub Pages

**Not implemented yet**
- User registration, login, OAuth / Google sign-in, and tenant isolation
- Persistent conversation history and database
- Document upload, embeddings, vector search, and RAG
- Live visitor chat, agent inbox, WebSocket events, and human handoff
- Billing, usage metering, admin controls, and production security review
- Training or fine-tuning a proprietary model

The interface is an early working frontend prototype. Live AI chat and content generation require a deployed backend and a configured model provider. The other modules are clearly marked as planned.

## Architecture

- **Frontend:** responsive HTML/CSS/JavaScript static app
- **API:** FastAPI / Python
- **Model integration:** configurable OpenAI-compatible chat completions endpoint
- **Knowledge retrieval:** planned PostgreSQL + pgvector
- **Deployment:** GitHub Pages for frontend; Docker/Render or another container host for backend
- **Secrets:** environment variables only; never put provider keys in frontend code or Git

## Run locally

1. Copy `.env.example` to `.env`.
2. Set `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` for your chosen OpenAI-compatible provider.
3. Start the backend:

```bash
docker compose up --build
```

4. Open the API docs at http://localhost:8000/docs.
5. Serve the `frontend` directory with any static web server and enter the backend URL in **Settings**. For example:

```bash
python -m http.server 5500 --directory frontend
```

Then open http://localhost:5500.

## Deploy the frontend to GitHub Pages

1. In the repository, open **Settings → Pages**.
2. Under **Build and deployment**, choose **GitHub Actions** as the source.
3. Push a change to `frontend/**` or manually run the **Deploy Synvoraith frontend to GitHub Pages** workflow.
4. The expected project site URL is:

   https://christian-tiaan.github.io/AI-Conversational-Intelligence-Platform/

5. After the backend is deployed, open the site, go to **Settings**, enter the backend URL, and test the API.

GitHub Pages hosts only the static frontend. It does not run the Python API or host model weights.

## Deploy the backend

The included `Dockerfile` and `render.yaml` are a starter blueprint for Render. Connect the repository to Render and configure these environment variables in the backend service:

- `APP_ENV=production`
- `AI_BASE_URL` — provider base URL, without the `/chat/completions` suffix
- `AI_API_KEY` — private provider key
- `AI_MODEL` — provider model identifier
- `CORS_ORIGINS` — exact deployed frontend origin, e.g. `https://christian-tiaan.github.io`

Do not commit API keys, user data, private datasets, or model weights.

## API endpoints

- `GET /health` — health check
- `GET /api/v1/status` — service and model configuration status
- `POST /api/v1/chat` — chat completion through the configured model endpoint

## Roadmap

1. Authentication, Google OAuth, and tenant isolation
2. Streaming chat and encrypted conversation persistence
3. Retrieval-augmented generation (RAG) with secure document ingestion
4. Content Studio templates and saved drafts
5. Live support inbox, WebSocket updates, and human handoff
6. Admin analytics, usage limits, billing, and monitoring
7. Model evaluation and optional LoRA/QLoRA fine-tuning pipeline

This repository is the application source of truth. Large model checkpoints and private datasets belong in secured artifact/object storage with versioned references in the project.
