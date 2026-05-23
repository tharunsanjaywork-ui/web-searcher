# Backend Schema — Data & Memory Architecture

## Data Storage
SearchMind does not use a traditional SQL/NoSQL database or a local ChromaDB instance.
All data is stored in **Firebase Firestore** (cloud-hosted database) with per-user data isolation.

## Firebase Firestore Collections

### Collection: `chat_messages`
Stores every user message and AI response across all sessions.

| Field | Type | Notes |
|---|---|---|
| message_id | string | Document ID (UUID generated per message) |
| session_id | string | Groups messages by conversation |
| user_id | string | Binds the message to the authenticated user |
| role | string | "user" or "assistant" |
| content | string | The actual message text or validated summary |
| timestamp | string | ISO-8601 UTC datetime |
| sources | string | JSON-stringified list of `{title, url}` sources (assistant only) |
| confidence | string | "high", "medium", or "low" (assistant only) |

### Collection: `users`
Stores user credentials for secure authentication.

| Field | Type | Notes |
|---|---|---|
| email | string | Document ID (lowercase, sanitized email string) |
| user_id | string | Unique user identifier hex string |
| password_hash | string | Password hashed securely using bcrypt |
| created_at | string | ISO-8601 UTC timestamp |

## Session Management
- Sessions are identified by a UUID `session_id`.
- `session_id` is generated on the client side and sent with every request.
- Messages are filtered by both `session_id` and `user_id` to provide secure access.

## Memory Strategy
- Firestore does not natively support vector similarity searches, so semantic memory is replaced by **chronological session memory**.
- On every new user message, the system retrieves the **last 5 chronological messages** from the same session and user.
- These are formatted as `[role]: content` and injected into the Summarizer Agent prompt as `memory_context`.
- Query Reformulator also retrieves up to the last 10 messages from the session to rewrite follow-up questions.

## API Endpoints

| Method | Route | Auth Required | Description |
|---|---|---|---|
| **GET** | `/` | No | Serves the main frontend `index.html` file |
| **POST** | `/api/register` | No (Rate Limited) | Registers a new user. Expects email/password, returns JWT token |
| **POST** | `/api/login` | No (Rate Limited) | Auths a user. Expects email/password, returns JWT token |
| **GET** | `/api/verify` | Yes | Verifies that a JWT token is valid |
| **POST** | `/api/chat` | Yes (Rate Limited) | Runs the four-agent pipeline and stores results in Firestore |
| **GET** | `/api/history` | Yes | Returns all session IDs for the user with preview text |
| **GET** | `/api/history/{session_id}` | Yes | Returns all messages in chronological order for a session |
| **POST** | `/api/new-session` | Yes | Generates and registers a new session UUID |

## Request Schema — POST /api/chat
```json
{
  "message": "string — the user's question",
  "session_id": "string — UUID of current session"
}
```

## Response Schema — POST /api/chat
All successful API responses are wrapped in `{"success": true, "data": {...}}`.
For `POST /api/chat`, the `data` payload contains:
```json
{
  "summary": "string — the validated summary",
  "sources": [
    {
      "title": "string",
      "url": "string"
    }
  ],
  "confidence": "string — high | medium | low",
  "session_id": "string"
}
```

---

## Agent Prompts

### Query Reformulator Agent Prompt
```text
You are a query reformulation expert.
The user is having a conversation and has just sent a new message.
Your job is to rewrite their message into a clear, standalone search query
that captures the FULL meaning including context from previous messages.

Previous conversation:
{conversation_history}

User's new message: "{message}"

Rules:
- If the message is already a clear standalone question, return it as-is
- If it contains pronouns like "it", "this", "that", "they" or is vague like "explain more", "tell me more", resolve them using conversation history
- Output ONLY the reformulated search query, nothing else
- Keep it concise — one clear sentence or question
```

### Summarizer Agent Prompt
```text
You are a precise research summarizer.
You have been given web search results for the query: "{query}"

The user's original message was: "{original_message}"

Previous conversation context:
{memory_context}

Web search results:
{search_results}

Your task:
- Summarize the search results clearly and factually
- Use the conversation context to understand follow-up questions
- If the user is asking for more detail on a previous topic, provide deeper information from the new search results
- Structure the summary with a main answer followed by key supporting points
- Keep it concise but complete
- Do not add information not found in the search results

Output only the summary. No preamble.
```

### Validator Agent Prompt
```text
You are a fact validation expert.
You have been given an AI-generated summary based on web search results.
Query: "{query}"
Summary to validate: "{summary}"
Your task:

Check if the summary accurately reflects what web search results would say
Identify any claims that seem uncertain, outdated, or potentially incorrect
Assign a confidence level: high, medium, or low

high: summary is factual, well-supported, no red flags
medium: summary is mostly correct but has some uncertain claims
low: summary contains claims that are likely incorrect or unverifiable

Output in this exact format:
VALIDATED_SUMMARY: [your corrected or confirmed summary]
CONFIDENCE: [high | medium | low]
REASON: [one sentence explaining the confidence level]
```