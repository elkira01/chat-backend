import logging
import re

from src.llm import generate_response

logger = logging.getLogger(__name__)


async def should_search_web(message: str) -> bool:
    """
    Decide if web search is needed by asking the LLM (Strategy B).
    Falls back to rule-based routing if the LLM request fails.
    """
    system_prompt = (
        "Reply SEARCH if this needs real-time web info, current events, "
        "or facts that might change, otherwise reply ANSWER."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    try:
        reply = await generate_response(messages)
        reply_upper = reply.strip().upper()
        logger.info(f"LLM reply: {reply_upper}")

        # The model might output things like "SEARCH." or "ANSWER."
        if "SEARCH" in reply_upper and "ANSWER" not in reply_upper:
            return True
        elif "ANSWER" in reply_upper and "SEARCH" not in reply_upper:
            return False
        # If the LLM generates a confusing answer, default to SEARCH if 'SEARCH' is in it
        if "SEARCH" in reply_upper:
            return True
        return False
    except Exception as e:
        logger.error(f"LLM routing failed, falling back to rules: {e}")
        return _rule_based_fallback(message)


def _rule_based_fallback(message: str) -> bool:
    keywords = [
        "today",
        "now",
        "current",
        "latest",
        "recent",
        "2024",
        "2025",
        "2026",
        "news",
        "update",
        "what happened",
        "who is",
        "price of",
        "how many",
        "search for",
        "i don't have",
    ]

    message_lower = message.lower()
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", message_lower):
            return True
    return False
