# Implementation Plan — Build Order

## Phase 1: Project Setup
- [x] Create project folder structure
- [x] Create requirements.txt with all dependencies (fastapi, uvicorn, PyJWT, bcrypt, firebase-admin, etc.)
- [x] Create .env file with all API keys and secrets
- [x] Create render.yaml for Render web service deployment configuration
- [x] Verify FastAPI runs with uvicorn locally
- ✅ Done when: FastAPI starts, serve_index returns index.html, no import errors

## Phase 2: Firebase Firestore Storage Layer
- [x] Initialize Firebase Admin SDK Certificate in firebase_config.py
- [x] Create connection client for Firebase Firestore
- [x] Write save_message() in memory.py — saves user/assistant messages with scoped metadata (session_id, user_id, content, timestamp, sources, confidence)
- [x] Write get_session_history() — retrieves all messages for a session scoped to user_id
- [x] Write get_memory_context() — retrieves last 5 chronological messages for contextual prompt grounding
- [x] Write get_all_sessions() — returns user's session list for sidebar previews (truncated preview of earliest user message)
- ✅ Done when: Messages can be written to and read from Firestore safely

## Phase 3: Agent Pipeline
- [x] Set up Tavily search tool (TavilySearchResults, max 5 results)
- [x] Write reformulate_query() (Agent 0) — uses last 10 messages of session history to output a standalone search query
- [x] Set up DeepSeek v4 Pro LLM via NVIDIA NIM API async client
- [x] Write summarizer_agent() (Agent 2) — takes query + original message + search results + memory context, returns summary text
- [x] Write validator_agent() (Agent 3) — takes query + summary, parses for VALIDATED_SUMMARY, CONFIDENCE, and REASON
- [x] Write run_pipeline() — orchestrates all four agents in sequential async fashion and handles empty results
- ✅ Done when: run_pipeline("test question", session, user) returns validated summary, sources, and confidence

## Phase 4: Authentication & FastAPI Routes
- [x] Write password hashing and verification helper functions using bcrypt in auth.py
- [x] Write register() and login() routes in auth.py using Firestore users collection and PyJWT token generation
- [x] Create JWT token verification middleware/helpers (`_get_user_id`)
- [x] POST /api/register — handles signup and issues token
- [x] POST /api/login — handles login and issues token
- [x] GET /api/verify — verifies current client token
- [x] POST /api/chat — protected chat pipeline route
- [x] GET /api/history and /api/history/{session_id} — protected chat history routes
- [x] Mount static files and homepage routes
- ✅ Done when: User can register, login, and chat securely using Bearer JWT tokens

## Phase 5: Frontend — Layout & Sidebar
- [x] Create index.html with single page layout
- [x] Add font links (Inter + JetBrains Mono)
- [x] Build floating glassmorphic background blobs and CSS float animations
- [x] Build Left Sidebar: 브랜드 로고 ("S" logo), New Chat button, scrollable history list, active list highlights, and user profile metadata footer
- [x] Build Main Area: Welcome screen with suggestions, message stream container, and auto-resizing input textarea with glowing send button
- ✅ Done when: Layout renders perfectly, matches styling brief, and suggestions work

## Phase 6: Frontend — Chat & Auth Integration
- [x] Form card toggles (Sign In / Sign Up states) and error feedback
- [x] Token verification on page load (retains user session) and Sign Out button logic
- [x] On send: disable controls, append user bubble immediately, scroll to bottom
- [x] Show dynamic timed stage labels ("Searching the web...", "Summarizing results...", "Validating answer...") on typing indicator
- [x] Render response card: parsed HTML paragraphs, domain favicons, and colored confidence badges
- [x] Load session history and reload sidebar on active changes
- ✅ Done when: The full user flow works end-to-end securely in the browser

## Phase 7: Error Handling & Polish
- [x] Create user-friendly error converter function `_friendly_error` (maps server timeouts, rate limits, and key issues)
- [x] Disable buttons and inputs during pipeline processing to prevent spamming
- [x] Escape HTML on client-side renders to protect against XSS injections
- [x] Standardize JSON response shapes (`{"success": true, "data": ...}`)
- ✅ Done when: Application handles all failures gracefully without console exceptions or crashes

## Phase 8: Deployment
- [x] Complete render.yaml configuration matching web runtime
- [x] Expose port 7860 and test multi-agent pipeline inside Docker container
- [x] Verify production variables (TAVILY_API_KEY, NVIDIA_API_KEY, SECRET_KEY, FIREBASE_CREDENTIALS_JSON) run flawlessly in cloud
- ✅ Done when: Live URL serves fully functional application state persistently