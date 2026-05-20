from src.prompt import (
    SYSTEM_MESSAGE_AUGMENTED,
    SYSTEM_MESSAGE_PLAIN,
    build_augmented_messages,
    build_plain_messages,
    trim_history,
)
from src.web.factory import SearchResult


def test_trim_history(mocker):
    mocker.patch("src.prompt.MAX_HISTORY_TURNS", 2)
    history = [
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "5"},
        {"role": "assistant", "content": "6"},
    ]
    trimmed = trim_history(history)
    assert len(trimmed) == 4
    assert trimmed[0]["content"] == "3"


def test_trim_history_invalid_type(mocker):
    mocker.patch("src.prompt.MAX_HISTORY_TURNS", "invalid")
    history = [{"role": f"user", "content": str(i)} for i in range(20)]
    trimmed = trim_history(history)
    assert len(trimmed) == 10  # Defaults to 5 turns = 10 messages


def test_build_plain_messages():
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    messages = build_plain_messages("how are you?", history)
    assert len(messages) == 4
    assert messages[0] == {"role": "system", "content": SYSTEM_MESSAGE_PLAIN}
    assert messages[1] == {"role": "user", "content": "hi"}
    assert messages[-1] == {"role": "user", "content": "how are you?"}


def test_build_augmented_messages():
    history = []
    results = [
        SearchResult(title="Title1", url="http://test.com", snippet="Snippet1", score=1)
    ]
    messages = build_augmented_messages("query", history, results)
    assert len(messages) == 2
    system_msg = messages[0]["content"]
    assert SYSTEM_MESSAGE_AUGMENTED in system_msg
    assert "Title1" in system_msg
    assert "http://test.com" in system_msg
    assert messages[1] == {"role": "user", "content": "query"}
