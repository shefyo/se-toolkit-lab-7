from __future__ import annotations

import json
import sys
from typing import Any

import requests

from config import load_config
from services.lms_api import LMSClient


SYSTEM_PROMPT = """
You are an LMS analytics bot.
Your job is to answer user questions by calling tools whenever backend data is needed.

Rules:
- For natural language questions about labs, students, scores, groups, completion, or analytics, use tools.
- Do not guess backend data.
- If the user asks what labs are available, call get_items.
- If the user asks for scores or pass rates for a lab, call get_pass_rates.
- If the user asks how many students are enrolled, call get_learners.
- If the user asks which lab has the lowest pass rate, first call get_items, then call get_pass_rates for each lab you discover, then compare.
- If the user asks which group is best in a lab, call get_groups.
- If the user asks for top students, call get_top_learners.
- If the input is a greeting, answer briefly and mention what you can do.
- If the input is gibberish or ambiguous, answer helpfully and suggest examples.
- Always produce concise, factual answers based on tool results.
""".strip()


def _cfg() -> dict[str, str | None]:
    return load_config()


def _client() -> LMSClient:
    cfg = _cfg()
    base_url = cfg.get("LMS_API_URL")
    api_key = cfg.get("LMS_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("Missing LMS_API_URL or LMS_API_KEY in .env.bot.secret")
    return LMSClient(base_url=base_url, api_key=api_key)


def get_tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "List labs and tasks available in the LMS backend",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get enrolled students and their groups",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution buckets for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab id like lab-04"}
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average scores or pass rates and attempt counts for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab id like lab-04"}
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submissions per day timeline for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab id like lab-04"}
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group performance, student counts, and scores for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab id like lab-03"}
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top learners overall or for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Optional lab id like lab-04"},
                        "limit": {"type": "integer", "description": "Number of learners to return"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab id like lab-05"}
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Refresh LMS data from the autochecker pipeline",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]


def _tool_impl(name: str, arguments: dict[str, Any]) -> Any:
    client = _client()

    if name == "get_items":
        return client.get_items()
    if name == "get_learners":
        return client.get_learners()
    if name == "get_scores":
        return client.get_scores(arguments["lab"])
    if name == "get_pass_rates":
        return client.get_pass_rates(arguments["lab"])
    if name == "get_timeline":
        return client.get_timeline(arguments["lab"])
    if name == "get_groups":
        return client.get_groups(arguments["lab"])
    if name == "get_top_learners":
        return client.get_top_learners(arguments.get("lab"), int(arguments.get("limit", 5)))
    if name == "get_completion_rate":
        return client.get_completion_rate(arguments["lab"])
    if name == "trigger_sync":
        return client.trigger_sync()

    raise RuntimeError(f"Unknown tool: {name}")


def _chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    cfg = _cfg()
    base_url = cfg.get("LLM_API_BASE_URL")
    api_key = cfg.get("LLM_API_KEY")
    model = cfg.get("LLM_API_MODEL")

    if not base_url or not api_key or not model:
        raise RuntimeError("Missing LLM_API_BASE_URL, LLM_API_KEY, or LLM_API_MODEL in .env.bot.secret")

    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def answer_with_tools(user_text: str) -> str:
    tools = get_tool_schemas()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    for _ in range(8):
        payload = _chat(messages, tools)
        choice = payload["choices"][0]["message"]

        tool_calls = choice.get("tool_calls") or []
        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": choice.get("content") or "",
                "tool_calls": tool_calls,
            })

            for call in tool_calls:
                function_name = call["function"]["name"]
                raw_args = call["function"].get("arguments") or "{}"
                try:
                    arguments = json.loads(raw_args)
                except json.JSONDecodeError:
                    arguments = {}

                print(f"[tool] LLM called: {function_name}({json.dumps(arguments, ensure_ascii=False)})", file=sys.stderr)

                try:
                    result = _tool_impl(function_name, arguments)
                except Exception as exc:
                    result = {"error": str(exc)}

                if isinstance(result, list):
                    print(f"[tool] Result: {len(result)} items", file=sys.stderr)
                else:
                    print("[tool] Result: object", file=sys.stderr)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=sys.stderr)
            continue

        content = (choice.get("content") or "").strip()
        if content:
            return content

    return "I could not complete the request. Please try rephrasing your question."
