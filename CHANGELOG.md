# Changelog

All notable changes to Resonode are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-06-27

### Added
- **Phase 1 foundation** — env-driven config, SQLite storage, and pluggable
  STT / LLM / memory interfaces so backends stay swappable.
- **Voice transcription core** — `/join` records a voice channel and `/leave`
  posts a speaker-attributed, timestamped transcript, transcribed **locally**
  with faster-whisper (no API key, audio never leaves your machine).
- **Slash commands** — `/join`, `/leave`, `/ping`, plus `/transcript`,
  `/search`, `/summary`, and `/ask` over stored history. No privileged Message
  Content intent required.
- **Streaming prototype** — near-real-time, per-utterance transcription behind
  `RESONODE_STREAMING=true`.
- **Brand kit** — original voice-core + memory-constellation icons and banners
  in `assets/resonode/`.
- **Project docs & infra** — Privacy Policy, Terms of Service, dressed-up README,
  build plan, GitHub Actions CI, Dependabot, issue templates, and contributor /
  security guides.

[Unreleased]: https://github.com/jlanguell/resonode/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jlanguell/resonode/releases/tag/v0.1.0
