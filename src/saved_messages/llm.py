import asyncio
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from saved_messages.config import settings


@dataclass(frozen=True)
class Classification:
    title: str
    tags: list[str]
    candidates: list[str]
    confidence: float


def _classify_sync(text: str, existing_tags: list[str]) -> Classification:
    model_path = Path(settings.llm_model_path)
    if not model_path.is_file():
        raise FileNotFoundError(
            f"LLM model not found at {model_path}; set LLM_MODEL_PATH or download the recommended GGUF"
        )
    model = _load_model(str(model_path))
    prompt = (
        "Classify this saved note. Return only a JSON object with keys title (short title), "
        "tags (one or two concise tags), candidates (up to three possible tags), and confidence "
        "(0..1). Prefer the user's existing tags when relevant. Use Russian if the note is in "
        "Russian. Existing tags: "
        + json.dumps(existing_tags, ensure_ascii=False)
        + "\nNote:\n"
        + text[:6000]
    )
    response = model.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": "You are a precise personal-notes organizer. Output valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=180,
    )
    content = response["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("LLM returned no text for the classification")
    parsed = json.loads(content)
    title = str(parsed["title"]).strip()[:240]
    tags = _clean_tags(parsed.get("tags", []))
    candidates = _clean_tags(parsed.get("candidates", []))
    confidence = float(parsed["confidence"])
    if not title or not 0 <= confidence <= 1:
        raise ValueError("LLM returned invalid title or confidence")
    candidates = list(dict.fromkeys([*tags, *candidates]))[:3]
    selected_tags = tags if confidence >= settings.llm_confidence_threshold else []
    return Classification(title, selected_tags, candidates, confidence)


def _clean_tags(values: object) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        raise ValueError("LLM returned invalid tags")
    return list(
        dict.fromkeys(str(value).strip().lower()[:80] for value in values if str(value).strip())
    )[:3]


@lru_cache(maxsize=1)
def _load_model(model_path: str):
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional local LLM dependency with `uv sync --extra llm`"
        ) from exc
    return Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=max(1, (os.cpu_count() or 2) - 1),
        verbose=False,
    )


async def classify(text: str, existing_tags: list[str]) -> Classification:
    return await asyncio.to_thread(_classify_sync, text, existing_tags)
