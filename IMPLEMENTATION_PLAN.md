# Implementation Plan — Build Order

## Phase 1: Project Setup
- [ ] Create project folder structure
- [ ] Create requirements.txt with all dependencies
- [ ] Create .env file with all three API keys
- [ ] Create render.yaml for Render deployment config
- [ ] Verify FastAPI runs with uvicorn locally
✅ Done when: FastAPI starts, / route returns 200, no import errors

## Phase 2: ChromaDB Memory Layer
- [ ] Initialize ChromaDB client with persistent path
- [ ] Create chat_messages collection
- [ ] Write save_message() function — saves user/assistant messages with metadata
- [ ] Write get_session_history() function — retrieves all messages for a session
- [ ] Write get_memory_context() function — semantic search for relevant past messages
- [ ] Write get_all_sessions() function — returns session list for sidebar
✅ Done when: Can save a message and retrieve it by session_id

## Phase 3: Agent Pipeline
- [ ] Set up Tavily search tool (TavilySearchResults, max 5 results)
- [ ] Write search_agent() — takes query, returns list of {title, url, content}
- [ ] Set up Gemini 2.5 Flash LLM via langchain-google-genai
- [ ] Write summarizer_agent() — takes query + search results + memory context, returns summary
- [ ] Write validator_agent() — takes query + summary, returns validated summary + confidence
- [ ] Write run_pipeline() — orchestrates all three agents in sequence
✅ Done when: run_pipeline("test question") returns summary, sources, and confidence

## Phase 4: FastAPI Routes
- [ ] POST /api/chat — calls run_pipeline(), saves to ChromaDB, returns response
- [ ] GET /api/history — returns all sessions from ChromaDB
- [ ] GET /api/history/{session_id} — returns all messages for session
- [ ] POST /api/new-session — returns new UUID session_id
- [ ] Mount static files route for serving frontend
✅ Done when: All endpoints return correct response shapes (test with curl or Postman)

## Phase 5: Frontend — Layout & Sidebar
- [ ] Create index.html with full page structure
- [ ] Add Tailwind CDN + Inter + JetBrains Mono fonts
- [ ] Build sidebar: logo, New Chat button, history list
- [ ] Build main area: welcome screen + chat thread container
- [ ] Build input bar: textarea + send button + keyboard listener
- [ ] Load chat history into sidebar on page load
✅ Done when: Layout renders correctly, sidebar shows, input bar works visually

## Phase 6: Frontend — Chat Functionality
- [ ] Generate session_id with crypto.randomUUID() on page load
- [ ] On send: append user message bubble immediately
- [ ] Show typing indicator with three-stage label updates
- [ ] Call POST /api/chat with message + session_id
- [ ] Render response card: summary + sources + confidence badge
- [ ] Add new session to sidebar after first message
- [ ] On sidebar click: load session history via GET /api/history/{session_id}
- [ ] New Chat button: generate new session_id + clear chat area
✅ Done when: Full chat flow works end to end — send message → see response card

## Phase 7: Error Handling & Edge Cases
- [ ] Show error card in chat thread if API call fails
- [ ] Disable send button while request is in progress
- [ ] Handle empty input — do not send
- [ ] Handle session with no history gracefully
- [ ] Handle ChromaDB read/write errors with fallback
✅ Done when: App does not crash on any failure — shows error messages instead

## Phase 8: Render Deployment
- [ ] Create render.yaml with web service config
- [ ] Set persistent disk config in render.yaml (/data mount)
- [ ] Set CHROMA_PATH=/data/chroma_db in Render env vars
- [ ] Set TAVILY_API_KEY and GOOGLE_API_KEY in Render env vars
- [ ] Deploy and verify all routes work on live URL
✅ Done when: App is live on Render, full pipeline works on production URL

## Phase 9: Final Polish
- [ ] Test all three confidence levels display correctly
- [ ] Test sidebar history loads correctly after page refresh
- [ ] Test mobile layout
- [ ] Verify source links open in new tab
- [ ] Verify memory context works — ask follow-up question that requires past context
✅ Done when: Full app works perfectly on both desktop and mobile on Render