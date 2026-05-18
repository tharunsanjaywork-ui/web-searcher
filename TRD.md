# Technical Requirements Document

## Why This Stack (Read This First)
FastAPI is chosen because the three-agent pipeline is async by nature — each agent
call (Tavily search, Gemini summarize, Gemini validate) is a network request that
benefits from async handling. FastAPI is the best Python framework for this.
LangChain is chosen because it has native Tavily integration, built-in memory
abstractions, and clean chain composition for multi-agent flows. Gemini 2.5 Flash
is chosen for summarization and validation because it is fast, handles long context
(full web search results) well, and has a generous free tier. ChromaDB is chosen
for cross-session memory because it runs embedded (no separate server), persists
to disk on Render, and integrates directly with LangChain memory.

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
  - LLM: Google Gemini 2.5 Flash via langchain-google-genai
  - Input: raw search results + summarization prompt
  - Output: clean structured summary

- Agent 3 — Validator Agent
  - LLM: Google Gemini 2.5 Flash via langchain-google-genai
  - Input: summary + validation prompt
  - Output: validated summary + confidence level (high / medium / low)

## Database / Memory
- Provider: ChromaDB (embedded, persistent)
- Purpose: Store all user messages and AI responses as vectors
- Embedding model: Google Generative AI Embeddings (models/embedding-001)
- LangChain integration: ConversationSummaryBufferMemory + Chroma vectorstore
- Persistence path: ./chroma_db (mapped to Render persistent disk)

## Authentication
- None in v1 — single user app

## File Storage
- None required

## Hosting
- Backend + Frontend: Render Web Service (Python runtime)
- Persistent disk: Render Disk mounted at /data for ChromaDB storage
- ChromaDB path on Render: /data/chroma_db

## Environment Variables
- TAVILY_API_KEY — Tavily web search API key
- GOOGLE_API_KEY — Google Gemini API key
- CHROMA_PATH — path to ChromaDB storage (default: ./chroma_db locally, /data/chroma_db on Render)

## Key Libraries
- fastapi — web framework
- uvicorn — ASGI server
- langchain — agent orchestration and memory
- langchain-google-genai — Gemini LLM and embeddings
- langchain-community — TavilySearchResults tool
- chromadb — vector database for memory
- python-dotenv — environment variable loading
- pydantic — request/response validation

## Hard Constraints
- Free tier only on Render
- No paid embedding API (use Google's free embedding model)
- No authentication in v1
- Must work in Antigravity without a build step