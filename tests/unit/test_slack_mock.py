from __future__ import annotations

import pytest

from ai_agent.mocks.base import ErrorInjectionConfig, RateLimitError
from ai_agent.mocks.slack import SlackMock


@pytest.fixture
def slack() -> SlackMock:
    mock = SlackMock()
    mock.add_channel("C001", "engineering")
    mock.add_channel("C002", "backend-team")
    return mock


def test_send_message_ok(slack: SlackMock) -> None:
    result = slack.send_message(channel="#engineering", text="hello")
    assert result["ok"] is True
    assert "ts" in result
    assert result["channel"] == "C001"


def test_send_message_without_hash(slack: SlackMock) -> None:
    result = slack.send_message(channel="engineering", text="hello")
    assert result["ok"] is True


def test_send_message_channel_not_found(slack: SlackMock) -> None:
    result = slack.send_message(channel="#nonexistent", text="hello")
    assert result["ok"] is False
    assert "channel_not_found" in result["error"]


def test_send_message_no_text(slack: SlackMock) -> None:
    result = slack.send_message(channel="#engineering", text="")
    assert result["ok"] is False


def test_list_channels(slack: SlackMock) -> None:
    result = slack.list_channels()
    assert result["ok"] is True
    names = [ch["name"] for ch in result["channels"]]
    assert "engineering" in names
    assert "backend-team" in names


def test_search_messages_finds_sent(slack: SlackMock) -> None:
    slack.send_message(channel="#engineering", text="deployment complete v2.4.1")
    result = slack.search_messages(query="v2.4.1")
    assert result["ok"] is True
    assert result["total"] == 1
    assert "v2.4.1" in result["messages"][0]["text"]


def test_search_messages_case_insensitive(slack: SlackMock) -> None:
    slack.send_message(channel="#engineering", text="Deploy done")
    result = slack.search_messages(query="DEPLOY")
    assert result["total"] == 1


def test_search_messages_no_match(slack: SlackMock) -> None:
    result = slack.search_messages(query="nothing-here")
    assert result["ok"] is True
    assert result["total"] == 0


def test_search_messages_missing_query(slack: SlackMock) -> None:
    result = slack.search_messages(query="")
    assert result["ok"] is False


def test_state_persists_between_calls(slack: SlackMock) -> None:
    slack.send_message(channel="#engineering", text="first")
    slack.send_message(channel="#engineering", text="second")
    result = slack.search_messages(query="first")
    assert result["total"] == 1


def test_error_injection_rate_limit() -> None:
    mock = SlackMock(error_config=ErrorInjectionConfig(force_error="rate_limit"))
    with pytest.raises(RateLimitError):
        mock.send_message(channel="#engineering", text="hello")


def test_error_injection_affects_all_methods() -> None:
    mock = SlackMock(error_config=ErrorInjectionConfig(force_error="server_error"))
    from ai_agent.mocks.base import ServerError
    with pytest.raises(ServerError):
        mock.list_channels()
