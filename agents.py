"""
SearchMind — Agent Pipeline
Four-step system: Reformulate → Search → Summarize → Validate
Uses Tavily for web search and Google Gemini 2.5 Flash for LLM calls.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from memory import get_memory_context, get_session_history, save_message

load_dotenv()

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


# --- Step 0: Query Reformulator ---

REFORMULATE_PROMPT = """You are a query reformulation expert.
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
- Keep it concise — one clear sentence or question"""


async def reformulate_query(message, session_id, user_id):
    """Rewrite vague follow-ups into clear search queries."""
    try:
        history = get_session_history(session_id, user_id)
        if not history or len(history) == 0:
            return message

        history_text = _format_conversation_history(history)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1,
        )

        prompt = REFORMULATE_PROMPT.format(
            conversation_history=history_text,
            message=message,
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        if not response or not response.content:
            return message

        reformulated = response.content.strip().strip('"')
        logger.info(f"Reformulated: '{message}' → '{reformulated}'")
        return reformulated
    except Exception as e:
        logger.error(f"Query reformulation failed: {e}")
        return message


def _format_conversation_history(history):
    """Format session history into readable conversation text."""
    if not history:
        return "No previous conversation."

    recent = history[-10:]
    parts = []
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if len(content) > 300:
            content = content[:300] + "..."
        parts.append(f"{role.upper()}: {content}")

    return "\n".join(parts)


# --- Step 1: Search Agent ---

async def search_agent(query):
    """Search the web using Tavily."""
    try:
        search_tool = TavilySearchResults(
            max_results=5,
            tavily_api_key=TAVILY_API_KEY
        )
        raw_results = await search_tool.ainvoke({"query": query})

        if not raw_results:
            logger.warning("Tavily returned empty results")
            return []

        if isinstance(raw_results, str):
            logger.warning(f"Tavily returned string: {raw_results}")
            return []

        results = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })
        return results
    except Exception as e:
        logger.error(f"Search agent failed: {e}")
        raise Exception(f"Web search unavailable: {e}")


# --- Step 2: Summarizer Agent ---

SUMMARIZER_PROMPT = """You are a precise research summarizer.
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

Output only the summary. No preamble."""


async def summarizer_agent(query, original_message, search_results,
                           memory_context):
    """Summarize search results using Gemini 2.5 Flash."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
        )

        formatted_results = _format_search_results(search_results)
        context = memory_context if memory_context else "No previous context."

        prompt = SUMMARIZER_PROMPT.format(
            query=query,
            original_message=original_message,
            memory_context=context,
            search_results=formatted_results,
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        if not response or not response.content:
            logger.warning("Gemini returned empty, retrying...")
            response = await llm.ainvoke([HumanMessage(content=prompt)])

        if not response or not response.content:
            raise Exception("Summarization returned empty response")

        return response.content
    except Exception as e:
        logger.error(f"Summarizer agent failed: {e}")
        raise Exception(f"Summarization failed: {e}")


def _format_search_results(results):
    """Format search results into readable text for the LLM."""
    if not results:
        return "No search results found."

    parts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        parts.append(f"[{i}] {title}\nURL: {url}\n{content}")

    return "\n\n".join(parts)


# --- Step 3: Validator Agent ---

VALIDATOR_PROMPT = """You are a fact validation expert.
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
REASON: [one sentence explaining the confidence level]"""


async def validator_agent(query, summary):
    """Validate summary using Gemini 2.5 Flash."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2,
        )

        prompt = VALIDATOR_PROMPT.format(query=query, summary=summary)
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        if not response or not response.content:
            return _fallback_validation(summary)

        return _parse_validation(response.content, summary)
    except Exception as e:
        logger.error(f"Validator agent failed: {e}")
        return _fallback_validation(summary)


def _parse_validation(response_text, original_summary):
    """Parse VALIDATED_SUMMARY / CONFIDENCE / REASON from response."""
    try:
        validated_summary = original_summary
        confidence = "medium"
        reason = "Validation completed"

        lines = response_text.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("VALIDATED_SUMMARY:"):
                validated_summary = stripped[len("VALIDATED_SUMMARY:"):].strip()
            elif stripped.startswith("CONFIDENCE:"):
                conf = stripped[len("CONFIDENCE:"):].strip().lower()
                if conf in ("high", "medium", "low"):
                    confidence = conf
            elif stripped.startswith("REASON:"):
                reason = stripped[len("REASON:"):].strip()

        if not validated_summary:
            validated_summary = original_summary

        return {
            "validated_summary": validated_summary,
            "confidence": confidence,
            "reason": reason,
        }
    except Exception as e:
        logger.error(f"Validation parsing failed: {e}")
        return _fallback_validation(original_summary)


def _fallback_validation(summary):
    """Return fallback validation when parsing fails."""
    return {
        "validated_summary": summary,
        "confidence": "medium",
        "reason": "Validation could not be completed",
    }


# --- Pipeline Orchestrator ---

async def run_pipeline(message, session_id, user_id):
    """Orchestrate the full pipeline with query reformulation."""
    try:
        # 1. Get memory context from ChromaDB
        memory_context = get_memory_context(session_id, user_id, message)

        # 2. Reformulate query using conversation history
        search_query = await reformulate_query(message, session_id, user_id)

        # 3. Run search agent with reformulated query
        search_results = await search_agent(search_query)

        # 4. Handle empty search results
        if not search_results:
            fallback_msg = "No web results found for this query."
            save_message(session_id, user_id, "user", message)
            save_message(session_id, user_id, "assistant", fallback_msg,
                         sources=[], confidence="low")
            return {
                "summary": fallback_msg,
                "sources": [],
                "confidence": "low",
                "session_id": session_id,
            }

        # 5. Run summarizer with both original message and reformulated query
        summary = await summarizer_agent(
            search_query, message, search_results, memory_context
        )

        # 6. Run validator agent
        validation = await validator_agent(search_query, summary)

        # 7. Save to ChromaDB
        source_list = [
            {"title": r["title"], "url": r["url"]}
            for r in search_results
        ]
        save_message(session_id, user_id, "user", message)
        save_message(
            session_id, user_id, "assistant",
            validation["validated_summary"],
            sources=source_list,
            confidence=validation["confidence"]
        )

        # 8. Return response
        return {
            "summary": validation["validated_summary"],
            "sources": source_list,
            "confidence": validation["confidence"],
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise Exception(f"Pipeline error: {e}")
