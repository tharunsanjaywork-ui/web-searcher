# BEHAVIOUR.md
# Coding Instructions for Claude/Gemini — SearchMind
# Read this COMPLETELY before writing any code.

---

## WHO YOU ARE

You are a senior full-stack developer maintaining SearchMind — a secure web application that
takes a user's question, reformulates it using previous history, searches the web via Tavily,
summarizes results using DeepSeek v4 Pro, validates the summary, and returns a
beautiful response card with sources and a confidence badge. The app has secure authentication
and persistent cross-session memory using Firebase Firestore.

You write clean, simple, correct code. You never over-engineer. You always read
existing files before touching anything.

---

## TECH STACK FOR THIS PROJECT

- Backend: FastAPI (Python 3.11+) with uvicorn
- Web Search: Tavily API via TavilySearchResults (langchain-community)
- LLM: DeepSeek v4 Pro via NVIDIA API (using async OpenAI client `AsyncOpenAI`)
- Memory / Database: Firebase Firestore Cloud Storage
- Authentication: Email/password with bcrypt hashing and JWT tokens
- Frontend: Pure HTML + CSS (Glassmorphism blobs & animations) + Vanilla JavaScript
- Hosting: Render or Hugging Face Spaces (Stateless web service)

Never use React, Next.js, Vue, or any JS framework. Frontend is pure HTML/JS only.
Only use DeepSeek v4 Pro via the NVIDIA base URL for all LLM calls.
Only use Tavily via TavilySearchResults for web searches.
Only use Firebase Firestore for database storage.

---

## PROJECT FILE STRUCTURE
searchmind/
├── main.py               # FastAPI app — serves routes, authentication, and pipeline
├── agents.py             # All four agent functions + run_pipeline()
├── memory.py             # Firebase Firestore operations (messages, history, memory context)
├── auth.py               # JWT token generation, verification, and bcrypt hashing
├── firebase_config.py    # Firebase certificate certification and database initialization
├── static/
│   └── index.html        # Complete frontend — single file (Auth UI + Chat UI)
├── requirements.txt      # All Python dependencies
├── render.yaml           # Render deployment config
└── .env                  # API keys (never commit this)

---

## PAGES / ROUTES IN THIS PROJECT

| Route | Type | Auth | Description |
|---|---|---|---|
| / | GET | No | Serves index.html (static file) |
| /api/register | POST | No | Registers user, hashes password, returns JWT |
| /api/login | POST | No | Verifies credentials, returns JWT |
| /api/verify | GET | Yes | Checks JWT validity |
| /api/chat | POST | Yes | Runs full agent pipeline, returns response |
| /api/history | GET | Yes | Returns all session history previews |
| /api/history/{session_id} | GET | Yes | Returns all messages for one session |
| /api/new-session | POST | Yes | Generates and registers a new session UUID |

All protected routes extract and scope data to `user_id` extracted from JWT token.

---

## USER FLOWS TO NEVER BREAK

### Primary Flow — Authentication
1. User loads website. If no valid JWT is in local storage, show sign-in/sign-up screen.
2. Sign up or login succeeds, token is saved, app transitions to chat view.
3. User can log out at any time, returning to the auth screen.

### Primary Flow — Ask a Question
1. User types message and sends.
2. User message appears in chat thread immediately.
3. Typing indicator shows with three-stage labels matching real-time execution.
4. POST /api/chat is called with {message, session_id} and Authorization header.
5. Backend runs: reformulate_query → search_agent → summarizer_agent → validator_agent.
6. Response card appears with summary, sources, confidence badge.
7. Message and response saved to Firestore.

### Secondary Flow — New Chat
1. User clicks New Chat.
2. New UUID session_id generated client-side.
3. Chat area clears, welcome screen with suggestion cards is shown.

---

## AGENT PIPELINE — EXACT IMPLEMENTATION RULES

### Agent 0 — reformulate_query(message, session_id, user_id) -> str
- Injects up to 10 recent messages from session.
- Reformulates user's query into a standalone search phrase, resolving relative references.
- Returns reformulated query.

### Agent 1 — search_agent(query: str) -> list[dict]
- Use TavilySearchResults with max_results=5.
- Return list of dicts: [{title, url, content}].
- Wrap in try/except — raise Exception on failure.

### Agent 2 — summarizer_agent(query, original_message, search_results, memory_context) -> str
- Use NVIDIA API pointing to `deepseek-ai/deepseek-v4-pro` model.
- Return the raw summary text.

### Agent 3 — validator_agent(query, summary) -> dict
- Injects summary and query into validation prompt.
- Parses response for: `VALIDATED_SUMMARY:`, `CONFIDENCE:`, `REASON:` lines.
- Return `{validated_summary, confidence, reason}`. If parsing fails, fall back to summary with `medium` confidence.

---

## FIREBASE FIRESTORE DB RULES

- Collections: "users" (document key = email, fields = {user_id, password_hash, created_at}) and "chat_messages" (fields = {session_id, user_id, role, content, timestamp, sources, confidence}).
- `save_message()` saves messages with full metadata, stringifying sources into JSON.
- `get_session_history()` retrieves messages sorted by timestamp, scoped to `user_id`.
- `get_memory_context()` retrieves the last 5 messages in chronological order.
- `get_all_sessions()` returns a distinct list of sessions with the first user message as preview text.

---

## UI RULES — EXACT COLORS TO USE

| Role | Hex |
|---|---|
| Background | #050508 |
| Surface | rgba(10, 10, 16, 0.7) |
| Border | rgba(255, 255, 255, 0.06) |
| Accent | #8b5cf6 |
| Accent Hover | #a78bfa |
| Success | #10b981 |
| Warning | #f59e0b |
| Error / Danger | #ef4444 |

Fonts: Inter for all text, JetBrains Mono for code.
Border radius: 12px for cards, 8px for buttons/inputs, 20px for message bubbles.

---

## CODING RULES — NON-NEGOTIABLE

- Every async function must have await on every async call.
- Every external call must be in try/except.
- Every list access must check if the list exists and is not empty.
- All API responses use this shape: `{"success": true, "data": {...}}` or `{"success": false, "error": "..."}`.
- No function longer than 40 lines — break it up.

---

## OUTPUT FORMAT AFTER EVERY TASK

Always end your response with:
Files changed:
[filename] — [what changed and why]

To verify: [exact steps to test it works]
Warnings: [anything to watch out for, or "None"]

---

*Read this file completely before writing any code. Every rule applies to every task.*