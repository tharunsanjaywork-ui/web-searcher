# Backend Schema — Data & Memory Architecture

## Data Storage
SearchMind does not use a traditional SQL/NoSQL database.
All data is stored in ChromaDB (vector database) with the following structure.

## ChromaDB Collections

### collection: chat_messages
Stores every user message and AI response across all sessions.

| Field | Type | Notes |
|---|---|---|
| id | string | UUID generated per message |
| document | string | The actual message text |
| session_id | string | Groups messages by conversation |
| role | string | "user" or "assistant" |
| timestamp | string | ISO format datetime |
| sources | string | JSON-stringified list of source URLs (assistant only) |
| confidence | string | "high", "medium", or "low" (assistant only) |

## Session Management
- Sessions are identified by a UUID session_id
- session_id is generated on the frontend (uuid library) and sent with every request
- No server-side session table — session_id is just a metadata filter on ChromaDB

## Memory Strategy
- On every new user message, LangChain queries ChromaDB for the top 5 most
  semantically similar past messages from the same session
- These are injected into the Summarizer Agent prompt as "conversation context"
- This gives the app cross-session memory without a separate DB

## API Endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | /api/chat | No | Run full pipeline, return response |
| GET | /api/history | No | Return all session IDs with first message preview |
| GET | /api/history/{session_id} | No | Return all messages for session |
| POST | /api/new-session | No | Return a new session_id UUID |

## Request Schema — POST /api/chat
```json
{
  "message": "string — the user's question",
  "session_id": "string — UUID of current session"
}
```

## Response Schema — POST /api/chat
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

## Sensitive Fields
- TAVILY_API_KEY — never returned in any response
- GOOGLE_API_KEY — never returned in any response

## Agent Prompts

### Summarizer Agent Prompt

You are a precise research summarizer.
You have been given web search results for the query: "{query}"
Previous conversation context:
{memory_context}
Web search results:
{search_results}
Your task:

Summarize the search results clearly and factually
Use the conversation context to understand any follow-up questions
Structure the summary with a main answer followed by key supporting points
Keep it concise but complete
Do not add information not found in the search results

Output only the summary. No preamble.

### Validator Agent Prompt
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