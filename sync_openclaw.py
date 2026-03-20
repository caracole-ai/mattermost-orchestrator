#!/usr/bin/env python3
"""
sync_openclaw.py
Reads OpenClaw runtime data and writes/updates a dashboard note in Obsidian.

Usage: python sync_openclaw.py
"""

import json
import os
from datetime import datetime, timezone


# --- Paths ---

SOURCES_DIR = os.path.expanduser("~/.openclaw/sources")
AGENTS_PATH = os.path.join(SOURCES_DIR, "agents.json")
TOKENS_PATH = os.path.join(SOURCES_DIR, "tokens.json")
EVENTS_PATH = os.path.join(SOURCES_DIR, "events.json")
PROJECTS_PATH = os.path.join(SOURCES_DIR, "projects.json")

OBSIDIAN_VAULT = os.path.expanduser("~/Documents/ObsidianVault")
DASHBOARD_DIR = os.path.join(OBSIDIAN_VAULT, "Dashboard")
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, "openclaw-runtime.md")


# --- Helpers ---

def load_json(path):
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    if not os.path.isfile(path):
        print(f"  [skip] {path} not found")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [error] reading {path}: {exc}")
        return None


def fmt_tokens(n):
    """Format a token count with thousands separators."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def fmt_cost(c):
    """Format a cost value in USD."""
    return f"${c:.2f}"


def fmt_timestamp(ts):
    """Shorten an ISO timestamp to a readable date+time."""
    if not ts:
        return "-"
    # Handle various ISO formats
    ts = ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]


# --- Section builders ---

def build_frontmatter(now_iso):
    lines = [
        "---",
        "titre: OpenClaw Runtime Dashboard",
        "type: dashboard",
        f"updated_at: {now_iso}",
        "---",
    ]
    return "\n".join(lines)


def build_agent_table(agents_data):
    if not agents_data:
        return "## Agents\n\n> No agent data available.\n"

    agents = agents_data.get("agents", [])
    if not agents:
        return "## Agents\n\n> No agents found.\n"

    lines = [
        "## Agents",
        "",
        "| Name | Emoji | Role | Team | Status | Model |",
        "|------|-------|------|------|--------|-------|",
    ]
    for a in agents:
        name = a.get("name", "?")
        emoji = a.get("emoji", "")
        role = a.get("role", "-")
        team = a.get("team", "-")
        status = a.get("status", "-")
        model = a.get("model", "-")
        # Shorten model name for readability
        model_short = model.split("/")[-1] if "/" in model else model
        lines.append(f"| {name} | {emoji} | {role} | {team} | {status} | `{model_short}` |")

    return "\n".join(lines)


def build_token_summary(tokens_data):
    if not tokens_data:
        return "## Token Consumption\n\n> No token data available.\n"

    usage_list = tokens_data.get("usage", [])
    if not usage_list:
        return "## Token Consumption\n\n> No usage records found.\n"

    # Aggregate per agent
    agent_totals = {}  # agentId -> {tokens, cost, sessions}
    for entry in usage_list:
        aid = entry.get("agentId", "unknown")
        tok = entry.get("tokens", {})
        cst = entry.get("cost", {})
        if aid not in agent_totals:
            agent_totals[aid] = {"input": 0, "output": 0, "total": 0, "cost": 0.0, "sessions": 0}
        agent_totals[aid]["input"] += tok.get("input", 0)
        agent_totals[aid]["output"] += tok.get("output", 0)
        agent_totals[aid]["total"] += tok.get("total", 0)
        agent_totals[aid]["cost"] += cst.get("total", 0.0)
        agent_totals[aid]["sessions"] += 1

    grand_tokens = sum(v["total"] for v in agent_totals.values())
    grand_cost = sum(v["cost"] for v in agent_totals.values())

    lines = [
        "## Token Consumption",
        "",
        "| Agent | Sessions | Input | Output | Total | Cost |",
        "|-------|----------|-------|--------|-------|------|",
    ]

    for aid in sorted(agent_totals, key=lambda k: agent_totals[k]["total"], reverse=True):
        v = agent_totals[aid]
        lines.append(
            f"| {aid} | {v['sessions']} | {fmt_tokens(v['input'])} | {fmt_tokens(v['output'])} "
            f"| {fmt_tokens(v['total'])} | {fmt_cost(v['cost'])} |"
        )

    lines.append(
        f"| **TOTAL** | **{sum(v['sessions'] for v in agent_totals.values())}** | | "
        f"| **{fmt_tokens(grand_tokens)}** | **{fmt_cost(grand_cost)}** |"
    )

    # Daily breakdown from aggregates
    daily = tokens_data.get("aggregates", {}).get("daily", {})
    if daily:
        lines.append("")
        lines.append("### Daily Breakdown")
        lines.append("")
        lines.append("| Date | Tokens | Cost | Agents |")
        lines.append("|------|--------|------|--------|")
        for date_str in sorted(daily.keys(), reverse=True):
            day = daily[date_str]
            day_agents = ", ".join(sorted(day.get("byAgent", {}).keys()))
            lines.append(
                f"| {date_str} | {fmt_tokens(day.get('totalTokens', 0))} "
                f"| {fmt_cost(day.get('totalCost', 0.0))} | {day_agents} |"
            )

    return "\n".join(lines)


def build_recent_activity(events_data, projects_data):
    """Build recent activity from events.json and project updates combined."""
    all_events = []

    # Events from events.json
    if events_data:
        for evt in events_data.get("events", []):
            ts = evt.get("timestamp", "")
            actor = evt.get("actor", "system")
            evt_type = evt.get("type", "")
            message = evt.get("data", {}).get("message", "")
            all_events.append({
                "timestamp": ts,
                "actor": actor,
                "type": evt_type,
                "message": message,
            })

    # Updates from projects.json (richer activity feed)
    if projects_data:
        for proj in projects_data.get("projects", []):
            proj_name = proj.get("name", proj.get("id", "?"))
            for upd in proj.get("updates", []):
                ts = upd.get("timestamp", "")
                agent = upd.get("agentId", "?")
                upd_type = upd.get("type", "update")
                message = upd.get("message", "")
                all_events.append({
                    "timestamp": ts,
                    "actor": agent,
                    "type": f"{proj_name}/{upd_type}",
                    "message": message,
                })

    if not all_events:
        return "## Recent Activity\n\n> No events recorded.\n"

    # Sort by timestamp descending, take last 20
    def sort_key(e):
        ts = e.get("timestamp", "")
        # Normalize timezone suffixes for sorting
        return ts.replace("Z", "+00:00")

    all_events.sort(key=sort_key, reverse=True)
    all_events = all_events[:20]

    lines = [
        "## Recent Activity",
        "",
        f"> Last {len(all_events)} events (most recent first)",
        "",
        "| Date | Actor | Type | Message |",
        "|------|-------|------|---------|",
    ]

    for evt in all_events:
        ts_short = fmt_timestamp(evt["timestamp"])
        actor = evt["actor"]
        etype = evt["type"]
        # Truncate long messages for table readability
        msg = evt["message"]
        if len(msg) > 120:
            msg = msg[:117] + "..."
        # Escape pipe characters in message
        msg = msg.replace("|", "\\|")
        lines.append(f"| {ts_short} | {actor} | {etype} | {msg} |")

    return "\n".join(lines)


def build_project_assignments(projects_data, agents_data):
    if not projects_data:
        return "## Project Assignments\n\n> No project data available.\n"

    projects = projects_data.get("projects", [])
    if not projects:
        return "## Project Assignments\n\n> No projects found.\n"

    # Build agent name lookup
    agent_names = {}
    if agents_data:
        for a in agents_data.get("agents", []):
            agent_names[a["id"]] = f"{a.get('emoji', '')} {a['name']}"

    lines = [
        "## Project Assignments",
        "",
        "| Project | Status | Tech | Assigned Agents | Last Update |",
        "|---------|--------|------|-----------------|-------------|",
    ]

    for proj in projects:
        name = proj.get("name", proj.get("id", "?"))
        status = proj.get("status", "-")
        tech_list = proj.get("tech", [])
        tech = ", ".join(tech_list) or "-"
        if len(tech) > 60:
            tech = tech[:57] + "..."

        # Assigned agents: from project's assignedTo field, or from agents.json projects field
        assigned_ids = set(proj.get("assignedTo", []))
        # Also check agents that list this project
        if agents_data:
            for a in agents_data.get("agents", []):
                if proj.get("id") in a.get("projects", []):
                    assigned_ids.add(a["id"])

        assigned = ", ".join(agent_names.get(aid, aid) for aid in sorted(assigned_ids)) or "-"
        last_update = proj.get("lastUpdate", "-")

        lines.append(f"| {name} | {status} | {tech} | {assigned} | {last_update} |")

    return "\n".join(lines)


# --- Main ---

def main():
    print("OpenClaw -> Obsidian sync")
    print("=" * 40)

    # Ensure output directory exists
    if not os.path.isdir(DASHBOARD_DIR):
        print(f"Creating directory: {DASHBOARD_DIR}")
        os.makedirs(DASHBOARD_DIR, exist_ok=True)

    # Load sources
    print("Loading data sources...")
    agents_data = load_json(AGENTS_PATH)
    tokens_data = load_json(TOKENS_PATH)
    events_data = load_json(EVENTS_PATH)
    projects_data = load_json(PROJECTS_PATH)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build sections
    sections = [
        build_frontmatter(now_iso),
        "",
        "# OpenClaw Runtime Dashboard",
        "",
        f"*Auto-generated on {now_iso} by `sync_openclaw.py`*",
        "",
        build_agent_table(agents_data),
        "",
        build_token_summary(tokens_data),
        "",
        build_recent_activity(events_data, projects_data),
        "",
        build_project_assignments(projects_data, agents_data),
        "",
    ]

    content = "\n".join(sections) + "\n"

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nDashboard written to: {OUTPUT_PATH}")
    print(f"  Size: {len(content)} chars, {content.count(chr(10))} lines")
    print("Done.")


if __name__ == "__main__":
    main()
