# Product Requirements Document

## App Name
SearchMind

## Tagline
Ask anything. Search the web. Get verified answers.

## Problem Being Solved
Users want web-search-powered AI answers — not just LLM hallucinations. They want
responses that are grounded in real current web data, clearly summarized, and
validated for accuracy. They also want the AI to remember past conversations so
they don't have to repeat context every session.

## Target User
Solo users, researchers, and developers who want a smarter search experience.
They are comfortable with web apps and expect a clean ChatGPT-like interface
with the added trust of web-grounded, validated answers.

## Core Features (Must Have)
- Multi-agent pipeline: Search → Summarize → Validate
- Web search via Tavily API (real-time web results)
- Summarization and validation via Google Gemini 2.5 Flash
- Cross-session memory using ChromaDB vector database
- Chat history sidebar (multiple conversations)
- New chat button
- Beautiful response cards with sources and validation badge
- Typing indicator while agents are processing
- Deploy-ready on Render

## Nice to Have (v2)
- Export chat as PDF
- Pin important chats
- Search through past conversations
- User accounts and login

## Out of Scope (This version will NOT include)
- Image or file uploads
- Voice input
- Multiple user accounts / authentication
- Mobile app

## User Stories
- As a user, I want to ask a question and get a web-grounded answer so I can trust it is current and accurate
- As a user, I want the app to remember what we discussed before so I don't repeat myself
- As a user, I want to see which sources the answer came from so I can verify myself
- As a user, I want to start a new chat so I can keep topics organized
- As a user, I want to see a validation badge so I know how reliable the answer is