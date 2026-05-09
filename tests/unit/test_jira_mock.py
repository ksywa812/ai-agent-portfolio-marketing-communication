from __future__ import annotations

import pytest

from ai_agent.mocks.base import ErrorInjectionConfig, RateLimitError
from ai_agent.mocks.jira import JiraMock


@pytest.fixture
def jira() -> JiraMock:
    return JiraMock()


def test_create_issue_ok(jira: JiraMock) -> None:
    result = jira.create_issue(title="Fix login bug", description="Broken on prod")
    assert result["ok"] is True
    assert result["key"] == "PROJ-1"
    assert result["status"] == "todo"
    assert "url" in result


def test_create_issue_auto_increments_key(jira: JiraMock) -> None:
    jira.create_issue(title="First")
    result = jira.create_issue(title="Second")
    assert result["key"] == "PROJ-2"


def test_create_issue_missing_title(jira: JiraMock) -> None:
    result = jira.create_issue(title="")
    assert result["ok"] is False


def test_get_issue_ok(jira: JiraMock) -> None:
    jira.create_issue(title="Bug report")
    result = jira.get_issue("PROJ-1")
    assert result["ok"] is True
    assert result["title"] == "Bug report"
    assert result["status"] == "todo"
    assert result["assignee"] is None


def test_get_issue_not_found(jira: JiraMock) -> None:
    result = jira.get_issue("PROJ-999")
    assert result["ok"] is False
    assert "issue_not_found" in result["error"]


def test_get_issue_case_insensitive(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    result = jira.get_issue("proj-1")
    assert result["ok"] is True


def test_transition_issue_todo_to_in_progress(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    result = jira.transition_issue("PROJ-1", "in_progress")
    assert result["ok"] is True
    assert result["status"] == "in_progress"


def test_transition_issue_with_assignee(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    result = jira.transition_issue("PROJ-1", "in_progress", assignee="pawelc")
    assert result["ok"] is True
    assert result["assignee"] == "pawelc"


def test_transition_issue_invalid(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    # todo → done is not a valid transition
    result = jira.transition_issue("PROJ-1", "done")
    assert result["ok"] is False
    assert "invalid_transition" in result["error"]


def test_transition_issue_not_found(jira: JiraMock) -> None:
    result = jira.transition_issue("PROJ-999", "in_progress")
    assert result["ok"] is False


def test_assign_issue(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    result = jira.assign_issue("PROJ-1", "anna")
    assert result["ok"] is True
    assert result["assignee"] == "anna"


def test_state_persists(jira: JiraMock) -> None:
    jira.create_issue(title="Bug")
    jira.transition_issue("PROJ-1", "in_progress", assignee="pawelc")
    fetched = jira.get_issue("PROJ-1")
    assert fetched["status"] == "in_progress"
    assert fetched["assignee"] == "pawelc"


def test_error_injection(jira: JiraMock) -> None:
    mock = JiraMock(error_config=ErrorInjectionConfig(force_error="rate_limit"))
    with pytest.raises(RateLimitError):
        mock.create_issue(title="Bug")
