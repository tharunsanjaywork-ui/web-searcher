# App Flow — All Pages & User Journeys

## All Pages / Screens
| Route | Page | Description |
|---|---|---|
| / | Main Chat UI | Single page app — sidebar + chat area + input |
| /api/chat | POST endpoint | Receives user message, runs pipeline, returns response |
| /api/history | GET endpoint | Returns list of all past chat sessions |
| /api/history/{session_id} | GET endpoint | Returns all messages for a specific session |
| /api/new-session | POST endpoint | Creates a new chat session, returns session_id |

## Navigation Structure
- Left sidebar (always visible on desktop)
- New Chat button at top of sidebar
- Chat history list below (each item = one session)
- Main chat area fills remaining width
- Input bar fixed at bottom of main area

## Entry Point
User opens the app. If no sessions exist, main area shows a welcome screen with
suggested questions. If sessions exist, the most recent session loads automatically.

## Core User Journey 1: Ask a Question
1. User types a question in the input bar
2. User presses Enter or clicks Send
3. User message appears immediately in the chat thread
4. Typing indicator appears (three dots animation) with label "Searching the web..."
5. Agent 1 runs — Tavily searches the web
6. Label updates to "Summarizing results..."
7. Agent 2 runs — Gemini summarizes
8. Label updates to "Validating answer..."
9. Agent 3 runs — Gemini validates
10. Response card appears with:
    - Summary text (formatted with markdown-like styling)
    - Sources section (list of clickable source links from Tavily)
    - Validation badge (✅ High Confidence / ⚠️ Medium Confidence / ❌ Low Confidence)
11. Message and response are saved to ChromaDB memory
12. Complete when: response card is fully displayed

## Core User Journey 2: Start a New Chat
1. User clicks "New Chat" in the sidebar
2. A new session_id is created via POST /api/new-session
3. Main chat area clears and shows welcome screen
4. New session appears at top of sidebar history list
5. All future messages in this session are stored under this session_id

## Core User Journey 3: Return to Past Chat
1. User clicks a past chat in the sidebar
2. GET /api/history/{session_id} is called
3. Full message history for that session loads in the main area
4. User can continue the conversation — memory context includes this session's history

## Empty States
- No chats yet: Show welcome card with app name, tagline, and 3 suggested questions
- Session has no messages: Show "Start by asking anything" placeholder

## Error States
- Tavily search fails: Show "Web search unavailable. Please try again." in red
- Gemini API fails: Show "AI service unavailable. Please try again." in red
- Network error: Show "Connection lost. Check your internet." in red
- All errors show as a system message card in the chat thread (not a popup)

## Redirect Logic
- On app load → load most recent session or show welcome screen
- After new session created → load that new empty session
- After clicking sidebar item → load that session's history
