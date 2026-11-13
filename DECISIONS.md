# Architectural decisions

## Model API

The agent uses the Anthropic Messages API for structured tool calls. A response can include several tool requests, which the loop executes sequentially before returning all results in one message. The model is configurable through `ANTHROPIC_MODEL`.

## Custom ReAct loop

The loop manages conversation messages, tool execution, error results, and an iteration limit directly. This keeps control flow visible and allows the agent to be tested with a simulated model client without a separate orchestration framework.

Conversation context is maintained within each request. The CLI retains an action history for the session, but starts a new model conversation for each request.

## In-memory service state

Slack, Calendar, Jira, and Email use shared in-memory stores. State survives tool calls and requests within a CLI session. Each test can create a fresh store without filesystem cleanup.

Cross-session persistence is not implemented. The `MOCK_PERSIST_STATE` setting is declared but is not connected to storage or serialization.

## Tool naming

Tool names use a double underscore between the service and operation, for example `slack__send_message`. This convention makes the service boundary visible in logs while keeping names compatible with the API tool schema.

## Service adapters

The project provides 11 tools across four services: Slack, Google Calendar, Jira, and Email. Each adapter defines an input schema and delegates execution to an injected service implementation. This supports workflows such as creating a Jira issue and sending a Slack notification.

The current adapters use mock services. Connecting real accounts requires implementing API clients and authentication.

## Input validation

The registry validates tool arguments with Pydantic before calling a service. The same models generate the JSON schemas supplied to the model API, keeping validation and tool definitions consistent.

Validation and execution errors become tool results so the agent can explain the failure or adjust its next action.

## Calendar seed data

Calendar events are anchored to the week starting May 4, 2026. Fixed dates keep sample data and tests reproducible. The system prompt uses the current local date and time, so relative requests such as "this week" may fall outside the seeded range.

## Structured logging

Structlog records agent iterations, tool calls, results, and failures as structured fields. The CLI also displays an action table and retains session history through `:history`.

## Deployment considerations

Using the agent with real workplace accounts would require durable storage where needed, per-user authentication, API adapters, and access controls. A shared deployment would also need request concurrency, token budgets, and tracing appropriate to its workload.
