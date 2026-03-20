from __future__ import annotations

from handlers.commands import (
    handle_fallback,
    handle_health,
    handle_help,
    handle_labs,
    handle_scores,
    handle_start,
)


def route_message(text: str) -> str:
    text = (text or "").strip()

    if text == "/start":
        return handle_start()
    if text == "/help":
        return handle_help()
    if text == "/health":
        return handle_health()
    if text == "/labs":
        return handle_labs()
    if text.startswith("/scores"):
        parts = text.split(maxsplit=1)
        lab_id = parts[1] if len(parts) > 1 else None
        return handle_scores(lab_id)

    return handle_fallback(text)
