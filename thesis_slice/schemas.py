"""Pydantic schemas + tolerant JSON extraction for model outputs."""
from __future__ import annotations

import json
import re
from typing import Dict

from pydantic import BaseModel


class WorkerOutput(BaseModel):
    files: Dict[str, str]   # path -> FULL new file contents (no diffs in the slice)
    notes: str = ""


class EvalVerdict(BaseModel):
    passed: bool = False
    reflexion: str = ""


def _extract_json(text: str) -> str:
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def parse_worker(text: str) -> WorkerOutput:
    return WorkerOutput.model_validate(json.loads(_extract_json(text)))


def parse_verdict(text: str) -> EvalVerdict:
    return EvalVerdict.model_validate(json.loads(_extract_json(text)))
