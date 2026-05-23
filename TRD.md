# Technical Requirements Document

## Why This Stack (Read This First)
FastAPI is chosen because the four-agent pipeline is async by nature — each agent
call (reformulate, Tavily search, DeepSeek summarize, DeepSeek validate) is a
network request that benefits from async handling. FastAPI is the best Python
framework for this. OpenAI's async client library is used to connect to the 
NVIDIA NIM API, which hosts DeepSeek v4 Pro at low latency. Firebase Firestore is
chosen for cross-session memory and user storage because it is fully managed,
requires no local disk infrastructure, and persists data in the cloud across deployments.

## Frontend
- Framework: Pure HTML + CSS (Glassmorphism blobs and floating animations) + Vanilla JavaScript
- Served directly by FastAPI as static files
- No build step required
- Single page application behavior using JS fetch calls and localStorage for JWT token persistence

## Backend
- Framework: FastAPI (Python 3.11+)
- All agent pipeline steps run as async functions called sequentially inside a pipeline orchestrator

## Agent Pipeline
- Agent 0 — Query Reformulator Agent
  - LLM: DeepSeek v4 Pro via NVIDIA API
  - Input: user query + last 10 messages from session
  - Output: standalone reformulated search query

- Agent 1 — Search Agent
  - Tool: TavilySearchResults (LangChain tool)
  - Input: reformulated search query
  - Output: raw web search results (list of title + url + content)

- Agent 2 — Summarizer Agent
  - LLM: DeepSeek v4 Pro via NVIDIA API
  - Input: raw search results + original query + conversation memory context (last 5 messages)
  - Output: clean structured summary

- Agent 3 — Validator Agent
  - LLM: DeepSeek v4 Pro via NVIDIA API
  - Input: summary + validation prompt
  - Output: validated summary + confidence level (high / medium / low) + reasoning sentence

## Database / Memory
- Provider: Firebase Firestore (cloud-hosted)
- Purpose: Store all user messages, AI responses, and user credentials
- Collections: chat_messages (conversations), users (authentication)
- No local disk persistence needed — all data lives in Firebase Firestore
- Memory context: retrieves last 5 messages from session (chronological)

## Authentication
- Email/password registration and login
- Password hashing: bcrypt
- Token format: JWT with HS256 algorithm
- User storage: Firebase Firestore "users" collection
- All API routes require Bearer token in Authorization header

## File Storage
- None required

## Hosting
- Backend + Frontend: Render Web Service (Python runtime) or Hugging Face Spaces
- No persistent disk required since storage is cloud-hosted via Firebase

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
- Must work without a build step