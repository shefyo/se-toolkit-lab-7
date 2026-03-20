from __future__ import annotations

from config import load_config
from services.lms_api import LMSClient


def _client() -> LMSClient:
    config = load_config()
    base_url = config.get("LMS_API_URL")
    api_key = config.get("LMS_API_KEY")

    if not base_url or not api_key:
        raise RuntimeError("Missing LMS_API_URL or LMS_API_KEY in .env.bot.secret")

    return LMSClient(base_url=base_url, api_key=api_key)


def handle_start() -> str:
    return (
        "Welcome to LMS Bot.\n"
        "Use /help to see available commands."
    )


def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start - welcome message\n"
        "/help - list available commands\n"
        "/health - backend health status\n"
        "/labs - list available labs\n"
        "/scores <lab> - show per-task pass rates"
    )


def handle_health() -> str:
    try:
        items = _client().get_items()
        return f"Backend is healthy. {len(items)} items available."
    except RuntimeError as exc:
        return f"Backend error: {exc}. Check that the services are running."


def handle_labs() -> str:
    try:
        items = _client().get_items()
    except RuntimeError as exc:
        return f"Backend error: {exc}. Check that the services are running."

    labs: dict[str, str] = {}
    for item in items:
        item_type = str(item.get("type", "")).lower()
        slug = item.get("slug") or item.get("id") or item.get("code") or ""
        title = item.get("title") or item.get("name") or slug

        if item_type == "lab" or str(slug).startswith("lab-"):
            labs[str(slug)] = str(title)

    if not labs:
        return "No labs found."

    lines = ["Available labs:"]
    for slug, title in sorted(labs.items()):
        lines.append(f"- {slug}: {title}")
    return "\n".join(lines)


def handle_scores(lab_id: str | None) -> str:
    if not lab_id:
        return "Usage: /scores <lab-id>"

    try:
        rows = _client().get_pass_rates(lab_id)
    except RuntimeError as exc:
        return f"Backend error: {exc}. Check that the services are running."

    if not rows:
        return f"No pass-rate data found for {lab_id}."

    lines = [f"Pass rates for {lab_id}:"]
    for row in rows[:20]:
        name = (
            row.get("task")
            or row.get("task_name")
            or row.get("title")
            or row.get("name")
            or "Unknown task"
        )

        percent = (
            row.get("pass_rate")
            or row.get("avg_score")
            or row.get("average")
            or row.get("value")
            or 0
        )

        attempts = (
            row.get("attempts")
            or row.get("count")
            or row.get("submissions")
            or 0
        )

        try:
            percent_value = float(percent)
        except (TypeError, ValueError):
            percent_value = 0.0

        if percent_value <= 1:
            percent_value *= 100

        try:
            attempts_value = int(attempts)
        except (TypeError, ValueError):
            attempts_value = 0

        lines.append(f"- {name}: {percent_value:.1f}% ({attempts_value} attempts)")

    return "\n".join(lines)


def handle_fallback(text: str) -> str:
    return f"Unknown command: {text}\nUse /help to see available commands."
