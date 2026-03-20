from __future__ import annotations


def handle_start() -> str:
    return "Welcome! Bot scaffold is working."

def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start\n"
        "/help\n"
        "/health\n"
        "/labs\n"
        "/scores <lab-id>"
    )

def handle_health() -> str:
    return "Backend status: not implemented yet."

def handle_labs() -> str:
    return "Labs list: not implemented yet."

def handle_scores(lab_id: str | None) -> str:
    if not lab_id:
        return "Usage: /scores <lab-id>"
    return f"Scores for {lab_id}: not implemented yet."

def handle_fallback(text: str) -> str:
    return f"Not implemented yet for input: {text}"
