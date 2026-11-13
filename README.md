# Intentio

Intentio is a command-line workplace automation agent. It takes requests in plain English and coordinates actions across Slack, Jira, Google Calendar, and email through a custom ReAct loop.

The service adapters currently use in-memory mock APIs. Requests exercise the full agent workflow without accessing external workplace accounts. The language model uses the Anthropic Messages API and requires an API key.

## Requirements

* Python 3.10 or newer
* [uv](https://docs.astral.sh/uv/) for dependency management
* An Anthropic API key

## Setup

From the repository directory, install dependencies:

```bash
uv sync --extra dev
```

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`:

```bash
cp .env.example .env
```

In PowerShell, use `Copy-Item .env.example .env`.

Optional settings include `ANTHROPIC_MODEL`, `AGENT_MAX_ITERATIONS`, `CURRENT_USER`, `LOG_LEVEL`, and `LOG_FILE`. Each request allows up to 10 model iterations by default.

## Usage

```bash
uv run python agent.py
```

Enter a request at the interactive prompt:

```text
You > Send a message to #engineering: deployment complete
You > Create a Jira ticket for the login bug, assign it to me, notify #backend-team
You > List my calendar events from May 4 to May 8, 2026 and find a free 2-hour slot
```

The agent displays tool calls, their results, and a final summary. It asks for clarification when a request lacks required details.

Available commands:

* `:help` displays commands and example requests.
* `:history` displays actions taken during the current session.
* `:exit` or `Ctrl+C` closes the application.

Mock data stays in memory for the CLI session. Calendar seed data uses the week starting May 4, 2026, so use that date range when exploring the seeded events. Cross-session persistence is not implemented.

## Architecture

The CLI passes requests to a ReAct loop. The model selects tools, the registry validates inputs, and the service adapters execute operations against a shared mock store. Results return to the model until it answers or reaches the iteration limit.

| Module | Responsibility |
| :--- | :--- |
| `ai_agent/cli/` | Interactive prompt, command handling, and action output |
| `ai_agent/agent/` | Agent loop, system prompt, and tool registry |
| `ai_agent/llm/` | Model API client with retries and timeouts |
| `ai_agent/tools/` | Schemas and adapters for 11 tools across four services |
| `ai_agent/mocks/` | In-memory services, seed data, and error injection |
| `ai_agent/config.py` | Environment settings and validation |
| `ai_agent/logging_setup.py` | Structured logging configuration |
| `tests/unit/` | Service, registry, and client tests |
| `tests/integration/` | Agent workflows with a simulated model client |

See [DECISIONS.md](DECISIONS.md) for architectural rationale and current limitations.

## Development

Run the test suite:

```bash
uv run pytest
```

Generate an HTML coverage report:

```bash
uv run pytest --cov-report=html
```

Run type checking and linting:

```bash
uv run mypy ai_agent/
uv run ruff check ai_agent/
```

Tests use a simulated model client and do not require a live API key. The test configuration enforces a minimum coverage of 80%.

## Error injection

Set a service error mode to exercise failure handling:

```bash
SLACK_FORCE_ERROR=rate_limit uv run python agent.py
JIRA_FORCE_ERROR=timeout uv run python agent.py
```

In PowerShell:

```powershell
$env:SLACK_FORCE_ERROR = "rate_limit"
uv run python agent.py
Remove-Item Env:SLACK_FORCE_ERROR
```

Supported variables are `SLACK_FORCE_ERROR`, `CALENDAR_FORCE_ERROR`, `JIRA_FORCE_ERROR`, and `EMAIL_FORCE_ERROR`. Valid modes are `rate_limit`, `timeout`, and `server_error`.
