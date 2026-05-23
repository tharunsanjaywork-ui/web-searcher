# App Flow — All Pages & User Journeys

## All Pages / Screens
| Route | Page / Endpoint | Description |
|---|---|---|
| / | Main UI | Single page app — starts at Auth screen, switches to main sidebar + chat area |
| /api/register | POST endpoint | Registers new email/password user, returns JWT token |
| /api/login | POST endpoint | Validates credentials, returns JWT token |
| /api/verify | GET endpoint | Checks if a JWT token is valid |
| /api/chat | POST endpoint | Receives user message, runs pipeline, returns response |
| /api/history | GET endpoint | Returns list of all past chat sessions for authenticated user |
| /api/history/{session_id} | GET endpoint | Returns all messages for a specific session for authenticated user |
| /api/new-session | POST endpoint | Creates a new chat session, returns session_id |

## Navigation Structure
- Left sidebar (always visible on desktop, collapses to hamburger menu on mobile)
- New Chat button at top of sidebar
- Chat history list below (each item = one session preview with truncated message)
- Main chat area fills remaining width
- Input bar fixed at bottom of main area
- User profile info at bottom of sidebar along with a logout icon

## Entry Point
User opens the app.
1. The app checks if a valid JWT token exists in `localStorage`.
2. If yes, it validates via `/api/verify` and displays the main chat UI.
3. If no (or expired), it displays the premium Glassmorphic Authentication Screen (Sign In / Sign Up).
4. Upon successful login/signup, the token is saved and the main chat UI is loaded.

## Core User Journey 0: Sign Up & Sign In
1. User loads the page and sees the glassmorphic Sign In card.
2. If they don't have an account, they click "Sign Up" which transitions the form mode.
3. They enter email and password, then press Enter or click the button.
4. On success, they are authenticated and redirected into the app.
5. They can click the logout button in the top left of the sidebar brand header at any time to clear credentials and return to the login screen.

## Core User Journey 1: Ask a Question
1. User types a question in the input bar and presses Enter or clicks Send.
2. User message appears immediately in the chat thread.
3. Typing indicator appears with dynamic stages:
   * "🔍 Searching the web..." (Agent 0 reformulates query, Agent 1 searches Tavily)
   * "📝 Summarizing results..." (Agent 2 summarizes results with DeepSeek v4 Pro)
   * "✅ Validating answer..." (Agent 3 validates summary for accuracy)
4. Response card appears with:
    - Summary text (formatted with line breaks)
    - Sources section (horizontal row of chips containing website favicon and domain, linking to source URLs)
    - Confidence badge (pill element: Green for High, Amber for Medium, Red for Low)
5. Message and response are saved to **Firebase Firestore** under `chat_messages` collection, scoped to the current `user_id`.

## Core User Journey 2: Start a New Chat
1. User clicks "New Chat" in the sidebar.
2. A new session_id is created (UUID).
3. Main chat area clears and shows the welcome screen.
4. New session appears in the sidebar history list after the first message is successfully sent.

## Core User Journey 3: Return to Past Chat
1. User clicks a past chat in the sidebar.
2. GET `/api/history/{session_id}` is called.
3. Full message history for that session loads chronologically in the main area.
4. User can continue the conversation — chronological history context is maintained.

## Empty States
- Welcome screen: shows a glowing logo, tagline, and three preset suggestion cards. Clicking a card automatically populates and submits the query.
- Session with no messages: shows suggestion cards.

## Error States
- All errors appear as custom status cards in the chat thread.
- If an API or backend error occurs, a styled red card is appended in-thread showing a friendly error message (e.g. rate limit alert, server timeout, or missing key error).

## Redirect Logic
- On app load → verify token → load history and most recent session, or show welcome screen.
- Logout → clear token → show auth screen.
