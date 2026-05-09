# DECISIONS.md

Key architectural decisions and the reasoning behind them.

---

## 1. Anthropic Claude over OpenAI GPT-4o

Anthropic was already the project dependency and the obvious choice for several reasons:

- **Parallel tool calls** — Claude can return multiple `tool_use` blocks in a single response. The agent loop processes all of them in one round-trip, which matters for multi-step scenarios like Scenario B where Jira and Slack calls can be batched.
- **Tool use quality** — Claude's function-calling is reliable and produces well-formed inputs consistently, which reduces the validation error rate in the registry layer.
- **Single dependency** — adding a second LLM provider would introduce unnecessary complexity for a prototype. The model is configurable via `ANTHROPIC_MODEL` in `.env` anyway.

---

## 2. Custom ReAct loop — no LangChain, LangGraph, or AutoGen

The custom loop keeps orchestration explicit and easy to inspect.

High-level agent frameworks abstract away the conversation history, tool call parsing, and retry logic. That abstraction costs you:
- **Predictability** — hard to know exactly what prompt is being sent
- **Token visibility** — frameworks often inject hidden system instructions
- **Debuggability** — when something goes wrong in a LangChain chain, the stack trace points into the framework, not your code

The custom loop in `agent/loop.py` is ~80 lines. It handles: conversation history as a growing message list, parallel tool calls in one turn, step limit, graceful error handling. Nothing here required a framework.

---

## 3. In-memory mock stores, not JSON files on disk

Service state can be stored in files or kept in memory.
I chose in-memory Python dicts instead:

- **Test isolation** — each test gets a fresh store with no cleanup required. JSON files would need to be deleted or reset between runs.
- **Speed** — no I/O in the hot path. Tests run in milliseconds.
- **Simplicity** — a dict is easier to inspect in a debugger than a file on disk.

The store lives for the duration of the agent session. Cross-session persistence is not implemented.

---

## 4. Tool names use double underscore (`slack__send_message`)

The Anthropic API rejects tool names containing dots. The natural human-readable format `slack.send_message` doesn't work. Options:
- `slackSendMessage` (camelCase) — hard to read in logs
- `slack_send_message` (flat underscore) — ambiguous service boundary
- `slack__send_message` (double underscore) — clear separator, readable, valid

Double underscore is the convention. It makes the service name immediately obvious in action traces and log output.

---

## 5. Four service adapters

The agent provides four service adapters (Slack, Calendar, Jira, Email):
- Email is the simplest mock to build (send + search, minimal state)
- Email supports workflows such as sending a summary of completed actions
- The tools module follows the same pattern for all four, so the marginal cost is low

---

## 6. Pydantic for tool input validation at the registry layer

The LLM can send malformed inputs — wrong types, missing required fields, out-of-range values. Rather than letting that propagate into the mock and cause cryptic errors, the registry validates every input against a Pydantic model before the mock method is called.

This means validation errors surface with clear messages (`field required`, `value is not a valid integer`) rather than a `KeyError` deep inside a mock method.

The Pydantic model also auto-generates the JSON schema sent to Claude via `model_json_schema()`. No duplication — the type hints are the single source of truth for both validation and the API contract.

---

## 7. Seed data anchored to a fixed week

Demo data is anchored to Monday 2026-05-04. The agent's system prompt injects real `datetime.now()` so date arithmetic works correctly (the LLM can compute "this week's" ISO range from the current date). But the seed events live in a fixed week so `list_events` always returns populated results regardless of when the demo runs.

This avoids the awkward situation where a calendar demo has zero events because the seed data was generated in the past.

---

## 8. Structlog over plain `logging`

Standard Python `logging` produces flat strings. `structlog` produces key-value records:

```
10:23:41 [info] tool_call tool=jira__create_issue input={'title': 'Login bug'}
10:23:41 [info] tool_result tool=jira__create_issue result={'ok': True, 'key': 'PROJ-4'}
```

During a demo or post-session review, being able to scan structured output and immediately see what tool was called with what parameters is worth the minor setup overhead.

---

## 9. What would change in production

This is a prototype. In a production system I would:

- **Persistent storage** — replace in-memory dicts with a real database (PostgreSQL) or at least Redis for session state
- **Authentication** — the `current_user` is currently a static config value; production needs OAuth per user
- **Observability** — add OpenTelemetry tracing so each agent run produces a trace with spans per tool call, latency metrics, and token usage
- **Async** — the agent loop is synchronous; for a multi-user platform it should be async (FastAPI + asyncio) with task queues (Celery or Cloud Tasks) for long-running runs
- **Real APIs** — replace mock classes with actual Slack/Jira/Google clients; the tool definitions stay the same, only the injected implementation changes
- **Rate limiting and quotas** — per-user LLM token budgets to control costs at scale
