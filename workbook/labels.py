"""Public display labels for trade partners (presentation layer only).

Rule (2026-11-05): a Cinderhaven dollar figure never shares a cell row with a
real retailer/distributor name. Cells show the label from the vendored
reference/retailer_display_labels.json instead. IDs, data keys and queries keep
the real names; only the values written into cells go through this module.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

LABELS_PATH = Path(__file__).resolve().parent.parent / "reference" / "retailer_display_labels.json"


@lru_cache(maxsize=1)
def _labels() -> dict[str, str]:
    """Map every partner ID and real name (lowercased) to its lowercase label."""
    data = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for group in ("retailers", "distributors"):
        for partner_id, entry in data[group].items():
            out[partner_id.lower()] = entry["label"]
            out[entry["name"].lower()] = entry["label"]
    return out


def _cap(label: str) -> str:
    return label[:1].upper() + label[1:]


def display_name(value: str) -> str:
    """Capitalized public label for a partner name or ID; other values unchanged."""
    if not value:
        return value
    label = _labels().get(value.lower())
    return _cap(label) if label else value


@lru_cache(maxsize=1)
def _text_pattern() -> re.Pattern:
    keys = sorted(_labels(), key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b", re.IGNORECASE)


def relabel_text(text: str) -> str:
    """Replace partner names/IDs inside free text with their lowercase labels."""
    if not text:
        return text
    return _text_pattern().sub(lambda m: _labels()[m.group(0).lower()], text)
