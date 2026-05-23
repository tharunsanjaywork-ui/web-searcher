"""
SearchMind — Agent Pipeline
Four-step system: Reformulate → Search → Summarize → Validate
Uses Tavily for web search and DeepSeek v4 Pro (via NVIDIA) for LLM calls.
"""

import os
import logging
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from memory import get_memory_context, get_session_history, save_message

load_dotenv()

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# DeepSeek v4 Pro via NVIDIA
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
LLM_MODEL = "deepseek-ai/deepseek-v4-pro"


def _get_llm_client():
    """Create async OpenAI client pointing to NVIDIA API."""
    return AsyncOpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
    )


async def _llm_call(prompt, temperature=0.3):
    """Call DeepSeek v4 Pro via NVIDIA API."""
    client = _get_llm_client()
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=0.95,
        max_tokens=500,
        extra_body={"chat_template_kwargs": {"thinking": False}},
    )
    return response.choices[0].message.content


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

        prompt = REFORMULATE_PROMPT.format(
            conversation_history=history_text,
            message=message,
        )

        result = await _llm_call(prompt, temperature=0.1)

        if not result:
            return message

        reformulated = result.strip().strip('"')
        logger.info(f"Reformulated: '{message}' -> '{reformulated}'")
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
        if not TAVILY_API_KEY:
            raise Exception("TAVILY_API_KEY is not set")

        search_tool = TavilySearchResults(
            max_results=3,
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

        logger.info(f"Search returned {len(results)} results for: {query}")
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
    """Summarize search results using DeepSeek v4 Pro."""
    try:
        formatted_results = _format_search_results(search_results)
        context = memory_context if memory_context else "No previous context."

        prompt = SUMMARIZER_PROMPT.format(
            query=query,
            original_message=original_message,
            memory_context=context,
            search_results=formatted_results,
        )

        result = await _llm_call(prompt, temperature=0.3)

        if not result:
            raise Exception("Summarization returned empty response")

        return result
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
        content = r.get("content", "")[:1000]
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
    """Validate summary using DeepSeek v4 Pro."""
    try:
        prompt = VALIDATOR_PROMPT.format(query=query, summary=summary)
        result = await _llm_call(prompt, temperature=0.2)

        if not result:
            return _fallback_validation(summary)

        return _parse_validation(result, summary)
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

async def _run_search_flow(message, session_id, user_id):
    """Run reformulation and web search sequentially."""
    try:
        search_query = await reformulate_query(message, session_id, user_id)
        search_results = await search_agent(search_query)
        return search_query, search_results
    except Exception as e:
        logger.error(f"Search flow failed: {e}")
        raise e


def _handle_empty_results(message, session_id, user_id, debug):
    """Handle assistant response when Tavily search returns no results."""
    fallback_msg = "No web results found for this query."
    save_message(session_id, user_id, "user", message)
    save_message(session_id, user_id, "assistant", fallback_msg,
                 sources=[], confidence="low")
    response = {
        "summary": fallback_msg,
        "sources": [],
        "confidence": "low",
        "session_id": session_id,
    }
    if debug:
        response["debug"] = {
            "tavily_results": [],
            "summarizer_output": fallback_msg,
            "validator_output": {
                "summary": fallback_msg,
                "confidence": "low",
                "reason": "No search results returned from Tavily."
            }
        }
    return response


def _save_and_format_response(message, session_id, user_id, search_results, summary, validation, debug):
    """Save assistant message to Firestore and format the pipeline output response."""
    source_list = [
        {"title": r.get("title", "Untitled"), "url": r.get("url", "")}
        for r in search_results
    ]
    save_message(session_id, user_id, "user", message)
    save_message(
        session_id, user_id, "assistant",
        validation.get("validated_summary") or summary,
        sources=source_list,
        confidence=validation.get("confidence") or "medium"
    )
    response = {
        "summary": validation.get("validated_summary") or summary,
        "sources": source_list,
        "confidence": validation.get("confidence") or "medium",
        "session_id": session_id,
    }
    if debug:
        response["debug"] = {
            "tavily_results": search_results or [],
            "summarizer_output": summary or "No output",
            "validator_output": {
                "summary": validation.get("validated_summary") or summary or "",
                "confidence": validation.get("confidence") or "medium",
                "reason": validation.get("reason") or "Validation completed successfully"
            }
        }
    return response


async def run_pipeline(message, session_id, user_id, debug: bool = False):
    """Orchestrate the full pipeline with query reformulation and optional debug tracing."""
    try:
        # 1. Fetch memory and run search flow in parallel
        memory_task = asyncio.to_thread(get_memory_context, session_id, user_id, message)
        flow_task = _run_search_flow(message, session_id, user_id)
        
        memory_context, flow_res = await asyncio.gather(memory_task, flow_task)
        search_query, search_results = flow_res

        # 2. Handle empty search results
        if not search_results:
            return _handle_empty_results(message, session_id, user_id, debug)

        # 3. Run summarizer and validator
        summary = await summarizer_agent(
            search_query, message, search_results, memory_context
        )
        validation = await validator_agent(search_query, summary)

        # 4. Save assistant response and return output
        return _save_and_format_response(
            message, session_id, user_id, search_results, summary, validation, debug
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise Exception(f"Pipeline error: {e}")
