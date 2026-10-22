"""Optional LLM explanation interface. Disabled unless GEMINI_API_KEY (or FRESHROOTS_LLM_PROVIDER=gemini) is set.

An explainer may only return a short note and a review category from a fixed
list. `attach_ai_notes` copies those two fields onto exception rows and never
touches calculations, quantities, actions or approval status.

This is the only module allowed to make a network call, and it only ever calls
the Gemini API. Nothing here can place or send an order.
"""
from __future__ import annotations

import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

import pandas as pd

REVIEW_CATEGORIES = ["Promotion or scheme", "New product", "Data error", "Seasonal effect", "Competitor action", "Unclear"]
FACT_FIELDS = ("sku_id", "code", "signal", "source_data", "rules_triggered")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_DEFAULT_MODEL = "gemini-flash-latest"

PROMPT = """You help a demand planner at an Indian FMCG company review one inventory exception.
Use only the facts below. Do not invent numbers, causes you cannot see, or quantities.
Do not recommend an order quantity or an action; the planner decides.
Write one or two plain sentences (under 60 words) saying what the planner should check first,
and pick the most likely review category.

Facts:
{facts}"""


class Explainer(Protocol):
    enabled: bool
    name: str

    def explain(self, facts: dict) -> tuple[str, str] | None:
        """Return (note, review_category) from the given facts only, or None."""


class DisabledExplainer:
    enabled = False
    name = "disabled"

    def explain(self, facts: dict) -> tuple[str, str] | None:
        return None


class GeminiExplainer:
    enabled = True
    name = "gemini"

    def __init__(self, api_key: str, model: str = GEMINI_DEFAULT_MODEL, timeout: float = 20.0):
        self._key = api_key
        self.model = model
        self.timeout = timeout

    def explain(self, facts: dict) -> tuple[str, str] | None:
        body = {
            "contents": [{"role": "user", "parts": [{"text": PROMPT.format(facts=json.dumps(facts, default=str, indent=2))}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {"note": {"type": "STRING"}, "category": {"type": "STRING", "enum": REVIEW_CATEGORIES}},
                    "required": ["note", "category"],
                },
            },
        }
        req = urllib.request.Request(
            GEMINI_URL.format(model=self.model), data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self._key},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        out = json.loads(text)
        return str(out.get("note", "")).strip(), str(out.get("category", "Unclear"))


def get_explainer(provider: str) -> Explainer:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if provider == "gemini" and key:
        return GeminiExplainer(key, os.environ.get("GEMINI_MODEL", "").strip() or GEMINI_DEFAULT_MODEL)
    # Anything else falls back to disabled rather than pretending an integration is present.
    return DisabledExplainer()


def attach_ai_notes(exceptions: pd.DataFrame, explainer: Explainer) -> pd.DataFrame:
    out = exceptions.copy()
    if not explainer.enabled or out.empty:
        return out
    rows = list(out.iterrows())

    def one(item):
        _, row = item
        try:
            return explainer.explain({k: row[k] for k in FACT_FIELDS})
        except Exception:  # a failed note leaves the exception untouched
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, rows))
    for (idx, _), result in zip(rows, results):
        if not result:
            continue
        note, category = result
        out.at[idx, "ai_note"] = str(note)[:500]
        out.at[idx, "ai_review_category"] = category if category in REVIEW_CATEGORIES else "Unclear"
    return out
