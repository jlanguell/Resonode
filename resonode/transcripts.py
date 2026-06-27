"""Pure helpers for turning stored utterances into readable transcripts."""
from __future__ import annotations

from typing import Iterable, Mapping


def format_timestamp(seconds: float) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def render_transcript(utterances: Iterable[Mapping], header: str | None = None) -> str:
    lines = [
        f"[{format_timestamp(u.get('start_s') or 0)}] {u.get('speaker_name')}: {u.get('text')}"
        for u in utterances
    ]
    body = "\n".join(lines)
    return (header + "\n" + body + "\n") if header else (body + "\n")
