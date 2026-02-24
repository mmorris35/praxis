"""AMP (Agent Memory Protocol) integration — pre-inference recall + post-inference learning."""

import os
import json
import requests
from typing import Optional

NELLIE_URL = os.environ.get("AMP_SERVER_URL", "http://100.87.147.89:8765")
AGENT_NAME = os.environ.get("AMP_AGENT", "jmo")


def _invoke(tool: str, arguments: dict) -> Optional[dict]:
    """Call an AMP-compliant MCP server."""
    try:
        resp = requests.post(
            f"{NELLIE_URL}/mcp/invoke",
            json={"name": tool, "arguments": arguments},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            return None
        return data.get("content")
    except Exception:
        return None


def recall(question: str, top_k: int = 5) -> list[dict]:
    """Pre-inference: search AMP for lessons relevant to this question.
    Returns list of {id, content, tags, created_at} dicts."""
    result = _invoke("search_lessons", {
        "agent": AGENT_NAME,
        "query": question,
        "limit": top_k,
    })
    if not result:
        return []
    # Nellie returns lessons as a list
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "lessons" in result:
        return result["lessons"]
    return []


def learn(question: str, correction: str, original_answer: str = "", tags: list[str] = None) -> Optional[str]:
    """Post-inference: store a correction as an AMP lesson.
    Returns the lesson ID if successful."""
    content = f"Q: {question}\n\nCorrection: {correction}"
    if original_answer:
        content += f"\n\nOriginal (wrong) answer: {original_answer}"

    if tags is None:
        tags = ["correction", "underwriting"]

    result = _invoke("add_lesson", {
        "agent": AGENT_NAME,
        "content": content,
        "tags": tags,
    })
    if result and isinstance(result, dict):
        return result.get("id")
    return None


def format_lessons_for_prompt(lessons: list[dict]) -> str:
    """Format AMP lessons into context for the LLM prompt."""
    if not lessons:
        return ""
    parts = ["## Institutional Knowledge (from prior corrections)\n"
             "IMPORTANT: If a lesson below directly answers the question, USE IT. "
             "These are verified corrections from senior underwriters.\n"]
    for i, lesson in enumerate(lessons, 1):
        # Handle Nellie's {distance, record: {content, ...}} format
        if "record" in lesson:
            record = lesson["record"]
            content = record.get("content", "")
            tags = record.get("tags", [])
        else:
            content = lesson.get("content", "")
            tags = lesson.get("tags", [])
        if content:
            parts.append(f"[Lesson {i}] {content}")
    return "\n\n".join(parts)
