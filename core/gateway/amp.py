"""AMP (Agent Memory Protocol) integration — DISABLED for CMMC-Buddy until we have CMMC-specific lessons."""

import os
import json
import requests
from typing import Optional

NELLIE_URL = os.environ.get("AMP_SERVER_URL", "http://100.87.147.88:8765")
AGENT_NAME = os.environ.get("AMP_AGENT", "cmmc-buddy")


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
    """Pre-inference: DISABLED - return empty until we have CMMC-specific lessons.
    This prevents JMO mortgage lessons from polluting CMMC answers."""
    return []


def learn(question: str, refinement: str, original_answer: str = "", tags: list[str] = None) -> Optional[str]:
    """Post-inference: store a refinement as an AMP lesson for CMMC-Buddy."""
    content = f"Q: {question}\n\nRefinement: {refinement}"
    if original_answer:
        content += f"\n\nOriginal (wrong) answer: {original_answer}"

    if tags is None:
        tags = ["refinement", "cmmc", "800-171"]

    result = _invoke("add_lesson", {
        "title": f"CMMC refinement: {question[:50]}...",
        "content": content,
        "tags": tags,
        "severity": "info",
    })
    if result and isinstance(result, dict):
        return result.get("id")
    return None


def format_lessons_for_prompt(lessons: list[dict]) -> str:
    """Format recalled lessons for inclusion in the LLM prompt."""
    if not lessons:
        return ""
    
    lines = ["## Institutional Knowledge (from previous refinements)\n"]
    for i, lesson in enumerate(lessons, 1):
        content = lesson.get("content", "")
        lines.append(f"{i}. {content}\n")
    
    return "\n".join(lines)
