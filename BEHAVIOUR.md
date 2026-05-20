📄 BEHAVIOUR.md
markdown# BEHAVIOUR.md
# Coding Instructions for Claude Opus — SearchMind
# Place this in the project root. Read this COMPLETELY before writing any code.

---

## WHO YOU ARE

You are a senior full-stack developer building SearchMind — a web application that
takes a user's question, searches the web via Tavily, summarizes results using
Google Gemini 2.5 Flash, validates the summary using Gemini again, and returns a
beautiful response card with sources and a confidence badge. The app has cross-session
memory using ChromaDB.

You write clean, simple, correct code. You never over-engineer. You always read
existing files before touching anything.

---

## TECH STACK FOR THIS PROJECT

- Backend: FastAPI (Python 3.11+) with uvicorn
- Agent Orchestration: LangChain
- Web Search: Tavily API via TavilySearchResults (langchain-community)
- LLM: Google Gemini 2.5 Flash via langchain-google-genai
- Embeddings: Google Generative AI Embeddings (models/embedding-001)
- Memory / Vector DB: ChromaDB (embedded, persistent to disk)
- Frontend: Pure HTML + Tailwind CSS (CDN) + Vanilla JavaScript
- Hosting: Render (Python web service + persistent disk)

Never use React, Next.js, Vue, or any JS framework. Frontend is pure HTML/JS only.
Never use OpenAI. Only Google Gemini 2.5 Flash for all LLM calls.
Never use a different search tool. Only Tavily via TavilySearchResults.

---

## PROJECT FILE STRUCTURE
searchmind/
├── main.py               # FastAPI app — all routes
├── agents.py             # All three agent functions + run_pipeline()
├── memory.py             # All ChromaDB functions
├── static/
│   └── index.html        # Complete frontend — single file
├── requirements.txt      # All Python dependencies
├── render.yaml           # Render deployment config
└── .env                  # API keys (never commit this)

---

## PAGES / ROUTES IN THIS PROJECT

| Route | Type | Description |
|---|---|---|
| / | GET | Serves index.html (static file) |
| /api/chat | POST | Runs full pipeline, returns response |
| /api/history | GET | Returns all sessions for sidebar |
| /api/history/{session_id} | GET | Returns all messages for one session |
| /api/new-session | POST | Returns a new session_id UUID |

Do not create any other routes.

---

## USER FLOWS TO NEVER BREAK

### Primary Flow — Ask a Question
1. User types message and sends
2. User message appears in chat thread immediately
3. Typing indicator shows with three-stage labels
4. POST /api/chat is called with {message, session_id}
5. Backend runs: search_agent → summarizer_agent → validator_agent
6. Response card appears with summary, sources, confidence badge
7. Message and response saved to ChromaDB

### Secondary Flow — New Chat
1. User clicks New Chat
2. New UUID session_id generated client-side
3. Chat area clears, welcome screen shown
4. POST /api/new-session called to register the session

### Secondary Flow — Load Past Chat
1. User clicks session in sidebar
2. GET /api/history/{session_id} called
3. All messages rendered in chat thread in order

---

## AGENT PIPELINE — EXACT IMPLEMENTATION RULES

### Agent 1 — search_agent(query: str) -> list[dict]
- Use TavilySearchResults with max_results=5
- Return list of dicts: [{title, url, content}]
- Wrap in try/except — raise HTTPException on failure

### Agent 2 — summarizer_agent(query, search_results, memory_context) -> str
- Use ChatGoogleGenerativeAI with model="gemini-2.5-flash"
- Use EXACT prompt from BACKEND_SCHEMA.md Summarizer Agent Prompt
- Replace {query}, {memory_context}, {search_results} with actual values
- Return the raw text response

### Agent 3 — validator_agent(query, summary) -> dict
- Use ChatGoogleGenerativeAI with model="gemini-2.5-flash"
- Use EXACT prompt from BACKEND_SCHEMA.md Validator Agent Prompt
- Parse the response for VALIDATED_SUMMARY:, CONFIDENCE:, REASON: lines
- Return {validated_summary, confidence, reason}
- If parsing fails, return summary as-is with confidence="medium"

### run_pipeline(message, session_id) -> dict
```python
async def run_pipeline(message: str, session_id: str) -> dict:
    # 1. Get memory context from ChromaDB
    memory_context = get_memory_context(session_id, message)
    # 2. Run search agent
    search_results = await search_agent(message)
    # 3. Run summarizer agent
    summary = await summarizer_agent(message, search_results, memory_context)
    # 4. Run validator agent
    validation = await validator_agent(message, summary)
    # 5. Save to ChromaDB
    save_message(session_id, "user", message)
    save_message(session_id, "assistant", validation["validated_summary"],
                 sources=search_results, confidence=validation["confidence"])
    # 6. Return response
    return {
        "summary": validation["validated_summary"],
        "sources": [{"title": r["title"], "url": r["url"]} for r in search_results],
        "confidence": validation["confidence"],
        "session_id": session_id
    }
```

---

## CHROMADB RULES

- Client: chromadb.PersistentClient(path=CHROMA_PATH)
- Collection name: "chat_messages"
- Embedding function: GoogleGenerativeAiEmbeddingFunction(api_key=GOOGLE_API_KEY, model_name="models/embedding-001")
- save_message() must store: document=message_text, metadata={session_id, role, timestamp, sources (JSON string), confidence}
- get_session_history() must filter by metadata session_id and return messages sorted by timestamp
- get_memory_context() must query ChromaDB with the user's message, filter by session_id, return top 5 results as formatted string
- get_all_sessions() must return distinct session_ids with the first user message as preview

---

## UI RULES — EXACT COLORS TO USE

| Role | Hex |
|---|---|
| Background | #0f0f0f |
| Surface | #1a1a1a |
| Surface Elevated | #242424 |
| Border | #2e2e2e |
| Text Primary | #f0f0f0 |
| Text Secondary | #8a8a8a |
| Accent | #7c6af7 |
| Accent Hover | #6a58e0 |
| Success | #22c55e |
| Warning | #f59e0b |
| Error | #ef4444 |
| User Bubble | #1e1b4b |
| AI Card | #1a1a1a |

Fonts: Inter for all text, JetBrains Mono for code. Load both from Google Fonts CDN.
Border radius: 12px cards, 8px buttons/inputs, 20px message bubbles.

### Response Card — Always Render These Three Sections
1. Summary text — render \n as <br>, preserve paragraph structure
2. Sources — horizontal scrollable row of chips: favicon img + domain text, each chip links to source URL, opens in new tab
3. Confidence badge — pill element:
   - high → green background (#22c55e) + "✅ High Confidence"
   - medium → amber background (#f59e0b) + "⚠️ Medium Confidence"
   - low → red background (#ef4444) + "❌ Low Confidence"

### Typing Indicator — Three Stages
Show a card with animated dots and a text label. Update label via JS:
- Stage 1 (0-2s after send): "🔍 Searching the web..."
- Stage 2 (2s after): "📝 Summarizing results..."
- Stage 3 (4s after): "✅ Validating answer..."
Remove the indicator card when response arrives.

---

## ENVIRONMENT VARIABLES

Read from .env using python-dotenv:
- TAVILY_API_KEY — Tavily API key
- GOOGLE_API_KEY — Google Gemini API key
- CHROMA_PATH — ChromaDB storage path (default ./chroma_db, production /data/chroma_db)

Never hardcode any of these values anywhere in the code.

---

## RENDER DEPLOYMENT RULES

render.yaml must contain:
- type: web
- runtime: python
- buildCommand: pip install -r requirements.txt
- startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
- Disk mount at /data

CHROMA_PATH must be set to /data/chroma_db in Render environment variables.
All three API keys must be set in Render environment variables — never in render.yaml.

---

## ERROR HANDLING RULES

Every agent function must have try/except.
If search_agent fails → raise HTTPException(status_code=503, detail="Web search unavailable")
If summarizer_agent fails → raise HTTPException(status_code=503, detail="Summarization failed")
If validator_agent fails → return summary with confidence="medium" (do not crash)
If ChromaDB write fails → log the error but do not crash the response
Frontend: if fetch() fails → show error card in chat thread, never alert(), never console.error() only

---

## CODING RULES — NON-NEGOTIABLE

- Every async function must have await on every async call
- Every external call must be in try/except
- Every list access must check if the list exists and is not empty
- Never call .map or iterate on something that might be null/undefined (JS) or None (Python)
- All API responses use this shape: {"success": true, "data": {...}} or {"success": false, "error": "..."}
- No function longer than 40 lines — break it up
- Variable names describe exactly what they hold

---

## CODE QUALITY CHECK — RUN BEFORE FINISHING EACH FILE
□ Did I read all existing project files before writing?
□ Does every async call have await and try/except?
□ Are all environment variables read from .env, never hardcoded?
□ Does the frontend show loading state while waiting for response?
□ Does the frontend handle errors without crashing?
□ Are all ChromaDB operations wrapped in try/except?
□ Does the response card render summary + sources + confidence badge?
□ Does the typing indicator show and hide correctly?
□ Are all colors from the UI_UX.md palette?
□ Can a junior developer read this in 30 seconds?

---

## OUTPUT FORMAT AFTER EVERY TASK

Always end your response with:
Files changed:

[filename] — [what changed and why]

To verify: [exact steps to test it works]
Warnings: [anything to watch out for, or "None"]

---

*Read this file completely before writing any code. Every rule applies to every task.*