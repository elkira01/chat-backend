import pytest

from src.router import _rule_based_fallback, should_search_web


def test_rule_based_fallback():
    assert _rule_based_fallback("what is the price of apple") == True
    assert _rule_based_fallback("tell me a story") == False
    assert _rule_based_fallback("who is the president") == True
    assert _rule_based_fallback("explain quantum physics") == False


@pytest.mark.asyncio
async def test_should_search_web_llm_search(mocker):
    mocker.patch("src.router.generate_response", return_value="SEARCH")
    result = await should_search_web("what is the weather today?")
    assert result == True


@pytest.mark.asyncio
async def test_should_search_web_llm_answer(mocker):
    mocker.patch("src.router.generate_response", return_value="ANSWER")
    result = await should_search_web("hello")
    assert result == False


@pytest.mark.asyncio
async def test_should_search_web_llm_confused_search(mocker):
    mocker.patch(
        "src.router.generate_response", return_value="I am confused but SEARCH ANSWER"
    )
    result = await should_search_web("hello")
    assert result == True


@pytest.mark.asyncio
async def test_should_search_web_llm_confused_no_search(mocker):
    mocker.patch(
        "src.router.generate_response",
        return_value="I am confused but I have an ANSWER",
    )
    result = await should_search_web("hello")
    assert result == False


@pytest.mark.asyncio
async def test_should_search_web_llm_complete_nonsense(mocker):
    mocker.patch(
        "src.router.generate_response",
        return_value="I have literally no idea what you mean",
    )
    result = await should_search_web("hello")
    assert result == False


@pytest.mark.asyncio
async def test_should_search_web_fallback(mocker):
    mocker.patch("src.router.generate_response", side_effect=Exception("API Error"))
    result = await should_search_web("news today")
    assert result == True
