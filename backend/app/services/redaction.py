from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"pat[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)(api[_ -]?key|token|secret)\s*[:=]\s*[A-Za-z0-9._/\-]{12,}"),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[redacted secret]", redacted)
    return redacted
