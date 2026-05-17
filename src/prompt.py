from .config import MAX_HISTORY_TURNS
from .web.factory import SearchResult

SYSTEM_MESSAGE_PLAIN = (
    "You are a helpful AI assistant. Answer the user's questions clearly and concisely."
)
SYSTEM_MESSAGE_AUGMENTED = (
    "You are a helpful AI assistant. You have access to real-time web search results."
)


def trim_history(history: list[dict]) -> list[dict]:
    """Trim the conversation history to the max allowed turns."""
    try:
        max_turns = int(MAX_HISTORY_TURNS)
    except (ValueError, TypeError):
        max_turns = 5

    # Each turn has 2 messages usually (user + assistant)
    max_messages = max_turns * 2
    if len(history) > max_messages:
        return history[-max_messages:]
    return history


def build_plain_messages(message: str, history: list[dict]) -> list[dict]:
    """Build messages for a plain request (no search)."""
    messages = [{"role": "system", "content": SYSTEM_MESSAGE_PLAIN}]
    messages.extend(trim_history(history))
    messages.append({"role": "user", "content": message})
    return messages


def build_augmented_messages(
    message: str, history: list[dict], search_results: list[SearchResult]
) -> list[dict]:
    """Build messages for a search-augmented request."""

    results_text = ""
    for i, res in enumerate(search_results, 1):
        results_text += f"[{i}] {res.title} | {res.url}\n    {res.snippet}\n"

    system_content = f"""{SYSTEM_MESSAGE_AUGMENTED}

--- Web Search Results ---
{results_text}
--- End of Results ---

Instruction: Use above results where relevant. Cite sources using their [number].
If unhelpful, use own knowledge and say so.
"""
    messages = [{"role": "system", "content": system_content}]
    messages.extend(trim_history(history))
    messages.append({"role": "user", "content": message})
    return messages
