# Mattermost AI Agents Orchestrator — Project Instructions

## Project Overview

Python orchestration system managing 3 AI agent bots (Winston, Amelia, John) on a Mattermost server. Each agent has a distinct personality and role — Architect, Full-Stack Developer, Project Manager — and they interact via the Mattermost REST API v4. The project uses the Anthropic Claude API for LLM-powered responses and supports both scripted conversations and live auto-response modes.

### Key Files

- `orchestrator.py` — Main entry point. `MattermostOrchestrator` class handles admin setup, team/channel/bot creation, and demo execution.
- `agents.py` — Agent class hierarchy with `Agent` base class and `Winston`, `Amelia`, `John` subclasses. Contains hardcoded fallback responses and LLM integration. Exports global instances `WINSTON`, `AMELIA`, `JOHN`.
- `agents_llm.py` — Alternative agent system using `AGENT_PERSONAS` dict for personality definitions. Contains `call_claude()`, `watch_and_respond()`, and the polling loop.
- `mattermost_client.py` — `MattermostClient` wrapper around Mattermost REST API v4. All HTTP calls go through `_request()`.
- `config.py` — Central configuration: server URL, tokens, `AGENTS` dict, `CHANNELS` dict. Loads `.env` via `python-dotenv`.
- `auto-respond.py` / `auto-respond-simple.py` — Live polling scripts that watch `#party-mode` for new messages from the admin user and trigger agent responses.
- `agent-react.py` — CLI tool to trigger agent reactions on a specific channel.
- `new-conversation.py` / `test-conversation.py` — Scripted multi-agent conversation demos.

### Stack

- Python 3.14, no framework
- `requests` for all HTTP (Mattermost API + Anthropic API)
- `python-dotenv` for environment configuration
- Virtual environment in `venv/`
- Mattermost server expected at `http://localhost:8065`

---

## Coding Principles

These are non-negotiable reflexes. Apply them systematically, without being asked.

### 1. Coherence first — follow existing patterns

Before writing new code, study how the codebase already solves similar problems. Key patterns to follow:

- **Agent definition**: Agents are defined as classes inheriting from `Agent` in `agents.py`, with `__init__` setting `name`, `role`, `emoji`, `personality`, `system_prompt`. Each agent overrides `think(context)` with keyword-matching logic and a fallback to `random.choice(self.thoughts)`.
- **Configuration**: All tokens, URLs, agent metadata, and channel definitions live in `config.py` as module-level constants loaded from `.env`. Never scatter config elsewhere.
- **API calls**: All Mattermost HTTP interactions go through `MattermostClient._request()`. Never call `requests.get/post` directly for Mattermost endpoints outside this client — except in `agents_llm.py` which has its own pattern for the polling loop.
- **Orchestrator flow**: Setup follows a strict sequence: `setup_admin()` -> `setup_team()` -> `setup_channels()` -> `setup_bots()`. Respect this order.
- **Message formatting**: Agents format messages via `Agent.format_message()` using the pattern `"{emoji} **{name}** ({role}):\n{content}"`.
- **Logging**: Use `logging.getLogger(__name__)` with `logging.basicConfig()`. Scripts use emoji prefixes in log messages for visual clarity.
- **Language**: All docstrings, comments, log messages, and agent responses are in **French**. Maintain this convention.

### 2. No hardcoded values — import from the source of truth

Never inline tokens, URLs, agent usernames, channel names, or API endpoints. Always import from `config.py` or read from `.env`. The authoritative sources are:

- **`config.py`** — `MATTERMOST_URL`, `API_BASE`, `ADMIN_TOKEN`, `ADMIN_USER_ID`, `AGENTS` dict, `CHANNELS` dict
- **`.env`** — All secrets (tokens, API keys). Never commit this file.
- **`agents.py`** — Agent class definitions and global instances (`WINSTON`, `AMELIA`, `JOHN`)

Exception: `agents_llm.py` and some test/demo scripts (`new-conversation.py`, `test-conversation.py`) currently contain hardcoded IDs (team IDs, bot user IDs, tokens). This is known technical debt — do not add more. When modifying these files, migrate hardcoded values to `config.py` or `.env`.

### 3. Verify types and signatures at the source

Before using a function, class, or data structure, read its actual definition. Do not rely on assumptions.

- Use Python type hints consistently. The codebase uses `typing.Dict`, `typing.Optional`, `typing.List` — follow this style.
- Check `MattermostClient` method signatures before calling them — parameter names and return types matter (methods return `Optional[Dict]`).
- Check the `AGENTS` and `CHANNELS` dict structures in `config.py` before accessing keys.
- Agent `think()` methods accept an optional `context: str` parameter — always pass context when available.

### 4. Edit over create

Prefer modifying an existing file over creating a new one. The project is intentionally flat (all `.py` files at root level). New files are justified only when they represent a genuinely new responsibility — not for slight variations of existing scripts.

### 5. SOLID — especially Single Responsibility

Each module has a clear responsibility:

- `config.py` — configuration only, no logic
- `mattermost_client.py` — HTTP transport only, no business logic
- `agents.py` — agent personalities and response generation only
- `orchestrator.py` — setup and coordination only

Respect these boundaries. Do not add Mattermost API calls to `agents.py`, do not add agent logic to `mattermost_client.py`.

### 6. Think smart, build to last

The goal is functional, stable, robust, maintainable. Write code that is simple enough to understand at a glance, but structured well enough to evolve. Prioritize:

- Graceful error handling (the codebase returns `None` on failure, never crashes silently)
- Idempotent operations (`get_or_create_bot`, `ensure_channel_exists`)
- Clear separation between setup, execution, and teardown

---

## Agent Personality Rules

When modifying agent behavior, respect these boundaries:

- **Winston** is the Architect: systems thinking, design patterns, scalability, infrastructure. He does NOT write code or discuss deadlines.
- **Amelia** is the Developer: implementation, code quality, frameworks, testing, performance. She does NOT make business decisions.
- **John** is the PM: deadlines, priorities, ROI, user value, team coordination. He does NOT make technical architecture choices.
- All agents respond exclusively in **French**.
- Agent responses must stay concise: 2-5 lines maximum, matching the `max_tokens` settings (300 in `agents.py`, 800 in `agents_llm.py`).
- Each agent has a distinct emoji identifier: Winston `🏗️`, Amelia `💻`, John `📋`. These must remain consistent across all files.

---

## Mattermost API Usage

- All API calls target Mattermost REST API **v4** at `{MATTERMOST_URL}/api/v4`.
- Authentication is via Bearer token in the `Authorization` header.
- Bot accounts are created via `/bots` endpoint, then given access tokens via `/users/{id}/tokens`.
- The orchestrator uses an admin token for privileged operations (creating bots, managing channels/teams) and individual bot tokens for posting messages as each agent.
- Channels use keys defined in `config.CHANNELS`: `orchestrator_log`, `agent_reflexions`, `party_mode`.
- Always check for existing resources before creating (`get_or_create_bot`, `ensure_channel_exists`) to ensure idempotency.

---

## Documentation & Memory

After every task that changes behavior, architecture, dependencies, or configuration, update the documentation **in the same commit**. This is not optional — undocumented changes are unfinished changes.

### 10. Keep docs in sync with code

When a task changes behavior, configuration, architecture, or tooling, identify which existing documentation describes that area and update it. Documentation lives in `README.md`, `README_LLM.md`, `USAGE.md`, `FINISH_SETUP.md`, `docs/`, and this `CLAUDE.md` — check all of them.

### 11. Update memory proactively

After completing a task, update Claude memory with any new facts that would help in future conversations: new files, changed configurations, new agent capabilities, API changes, known limitations. Remove or correct stale information.

### 12. Clean the obsolete

When updating documentation, don't just append — read what's already there and remove or correct anything that no longer reflects the project's state. The project has some stale references (hardcoded IDs in test scripts, outdated team IDs) — clean these when encountered.

---

## Autonomous Decision-Making

These principles govern how Claude evaluates incoming tasks and decides when to self-organize.

### 7. Evaluate complexity before acting

For every request, assess its scope and complexity before writing code:

- **Simple** (1-3 files, single concern, clear path): execute directly.
- **Medium** (4-6 files, 2-3 concerns, some ambiguity): enter plan mode, draft a brief plan, then execute.
- **Complex** (all core modules, cross-cutting concerns, new agent or new integration): enter plan mode, design a structured plan with phases, then recruit a feature team of agents with precise briefs.

### 8. Trigger planning autonomously

Do not wait for the user to ask for a plan. When complexity is medium or above, **enter plan mode on your own**: outline the approach, identify the files and concerns involved, flag risks, and present the plan before executing.

### 9. Recruit agents strategically

When a task is parallelizable (independent subtasks across different files or subsystems), recruit specialized agents. Each agent must receive:
- A **clear mission scope** (which files, which changes)
- **Full context** (imports, patterns, conventions, constraints from this document)
- **Explicit rules** (what to do, what NOT to do)
- **Autonomy to read** the code they need before editing

---

## Python Conventions

- Follow **PEP 8** for all Python code.
- Use `snake_case` for functions, methods, and variables. Use `PascalCase` for classes. Use `UPPER_SNAKE_CASE` for module-level constants.
- Docstrings on every module, class, and public function — in French, matching the existing style (short one-liners or triple-quoted blocks).
- Type hints on all function signatures: use `Optional[Dict]`, `List[tuple]`, `str`, etc.
- Imports: standard library first, then third-party (`requests`, `dotenv`), then local modules (`config`, `mattermost_client`, `agents`). No blank lines within groups, one blank line between groups.
- Error handling: return `None` or `False` on failure with a `logger.error()` call. Do not raise exceptions for recoverable API errors.
- No new dependencies without explicit approval. The project deliberately keeps a minimal footprint (`requests` + `python-dotenv`).
