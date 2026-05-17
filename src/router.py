import re


def should_search_web(message: str) -> bool:
    """
    Decide if web search is needed based on rule-based keywords.
    """
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
    ]

    message_lower = message.lower()
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", message_lower):
            return True
    return False
