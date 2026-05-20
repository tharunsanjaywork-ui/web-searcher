# Technical Requirements Document

## Why This Stack (Read This First)
FastAPI is chosen because the four-agent pipeline is async by nature — each agent
call (reformulate, Tavily search, DeepSeek summarize, DeepSeek validate) is a
network request that benefits from async handling. FastAPI is the best Python
framework for this. LangChain is chosen because it has native Tavily integration
and clean chain composition for multi-agent flows. DeepSeek v4 Pro (via NVIDIA
API) is chosen for summarization and validation because it is fast, handles long
context (full web search results) well, and is accessed through an OpenAI-compatible
endpoint. Firebase Firestore is chosen for cross-session memory and user storage
because it is fully managed, requires no infrastructure, and persists data in the
cloud across deployments.

## Frontend
- Framework: Pure HTML + Tailwind CSS (CDN) + Vanilla JavaScript
- Served directly by FastAPI as static files
- No build step required — Antigravity-friendly
- Single page application behavior using JS fetch calls

## Backend
- Framework: FastAPI (Python 3.11+)
- Agent orchestration: LangChain
- All three agents run as async functions called sequentially

## Agent Pipeline
- Agent 1 — Search Agent
  - Tool: TavilySearchResults (LangChain tool)
  - Input: user query
  - Output: raw web search results (list of title + url + content)

- Agent 2 — Summarizer Agent
  - LLM: DeepSeek v4 Pro via NVIDIA API (OpenAI-compatible endpoint)
  - Input: raw search results + summarization prompt
  - Output: clean structured summary

- Agent 3 — Validator Agent
  - LLM: DeepSeek v4 Pro via NVIDIA API (OpenAI-compatible endpoint)
  - Input: summary + validation prompt
  - Output: validated summary + confidence level (high / medium / low)

## Database / Memory
- Provider: Firebase Firestore (cloud-hosted)
- Purpose: Store all user messages, AI responses, and user accounts
- Collections: chat_messages (conversations), users (authentication)
- No local disk persistence needed — all data lives in Firebase
- Memory context: retrieves last 5 messages from session (chronological)

## Authentication
- Email/password registration and login
- Password hashing: bcrypt
- Token format: JWT (PyJWT) with HS256 algorithm
- User storage: Firebase Firestore "users" collection
- All API routes require Bearer token in Authorization header

## File Storage
- None required

## Hosting
- Backend + Frontend: Render Web Service (Python runtime)
- Persistent disk: Render Disk mounted at /data for ChromaDB storage
- ChromaDB path on Render: /data/chroma_db

## Environment Variables
- TAVILY_API_KEY — Tavily web search API key
- NVIDIA_API_KEY — NVIDIA API key (for DeepSeek v4 Pro)
- SECRET_KEY — JWT signing key (minimum 32 characters)
- FIREBASE_CREDENTIALS_PATH — path to Firebase service account JSON (local dev)
- FIREBASE_CREDENTIALS_JSON — base64-encoded service account JSON (cloud deploy)

## Key Libraries
- fastapi — web framework
- uvicorn — ASGI server
- langchain — agent orchestration
- langchain-openai — OpenAI-compatible LLM client
- langchain-community — TavilySearchResults tool
- openai — async client for NVIDIA/DeepSeek API
- firebase-admin — Firebase Firestore client
- python-dotenv — environment variable loading
- pydantic — request/response validation
- PyJWT — JWT token creation and verification
- bcrypt — password hashing
- slowapi — API rate limiting

## Hard Constraints
- Free tier on Render / HF Spaces
- Firebase Spark (free tier) for Firestore
- JWT-based authentication (email/password)
- Must work in Antigravity without a build step