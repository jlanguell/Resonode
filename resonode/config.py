"""Resonode configuration — environment-driven, local-first defaults.

Everything the bot needs is read from environment variables (loaded from .env by
the entrypoint). Defaults favour the private/local path; cloud backends are
opt-in. This object is passed to every service so nothing reads os.environ
directly.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _get(name: str, default=None):
    return os.getenv(name, default)


def _flag(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _int_or_none(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


@dataclass
class Config:
    token: str | None = None
    prefix: str = "!"

    # Speech-to-text
    stt_backend: str = "local"          # "local" | "deepgram"
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    deepgram_api_key: str | None = None

    # LLM (summaries / translation / moderation) — bring your own key
    llm_provider: str = "none"          # "none" | "openai" | "anthropic"
    llm_model: str = ""
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Memory ("server brain")
    memory_backend: str = "keyword"     # "keyword" (now) | "vector" (roadmap)

    # Storage
    db_path: str = ""
    recordings_dir: str = ""
    transcripts_dir: str = ""

    # Feature flags
    streaming: bool = False
    auto_summary: bool = False

    # Register slash commands instantly in this one guild while testing (optional).
    dev_guild_id: int | None = None

    @classmethod
    def from_env(cls) -> "Config":
        base = BASE_DIR
        return cls(
            token=_get("DISCORD_TOKEN"),
            prefix=_get("COMMAND_PREFIX", "!"),
            stt_backend=(_get("RESONODE_STT", "local") or "local").lower(),
            whisper_model=_get("WHISPER_MODEL", "base"),
            whisper_device=_get("WHISPER_DEVICE", "cpu"),
            deepgram_api_key=_get("DEEPGRAM_API_KEY"),
            llm_provider=(_get("RESONODE_LLM", "none") or "none").lower(),
            llm_model=_get("RESONODE_LLM_MODEL", ""),
            openai_api_key=_get("OPENAI_API_KEY"),
            anthropic_api_key=_get("ANTHROPIC_API_KEY"),
            memory_backend=(_get("RESONODE_MEMORY", "keyword") or "keyword").lower(),
            db_path=_get("RESONODE_DB", str(base / "resonode.db")),
            recordings_dir=_get("RESONODE_RECORDINGS", str(base / "recordings")),
            transcripts_dir=_get("RESONODE_TRANSCRIPTS", str(base / "transcripts")),
            streaming=_flag("RESONODE_STREAMING", False),
            auto_summary=_flag("RESONODE_AUTO_SUMMARY", False),
            dev_guild_id=_int_or_none(_get("RESONODE_DEV_GUILD")),
        )

    @property
    def compute_type(self) -> str:
        # int8 is fast/light on CPU; float16 is a better default on a CUDA GPU.
        return "float16" if self.whisper_device == "cuda" else "int8"
