# Contributing to Resonode

Thanks for your interest in improving Resonode! This is an early,
building-in-public project, so issues, ideas, and pull requests are all welcome.

## Getting set up

```powershell
git clone https://github.com/jlanguell/resonode.git
cd resonode
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add a bot token from the
[Discord Developer Portal](https://discord.com/developers/applications) to run
the bot locally. See the [README](README.md) for the full quickstart and
[BUILD_PLAN.md](BUILD_PLAN.md) for the architecture.

## Running the tests

The core logic is covered by sandbox unit tests that need **no Discord token**:

```powershell
.\.venv\Scripts\python.exe tests\test_core.py
```

CI runs these on every push and pull request. Please make sure they pass before
opening a PR, and add tests for new pure-logic code where practical.

## Code style & architecture

- Python 3.11+, standard library plus the dependencies in `requirements.txt`.
- Keep cogs thin; STT, LLM, memory, and storage live behind interfaces
  (`resonode/stt.py`, `services.py`, `storage.py`) so backends stay swappable.
- Commands are **slash commands** (`@discord.slash_command`); long operations
  call `defer()` so they don't hit Discord's 3-second response limit.
- Match the surrounding style and keep changes focused.

## Pull requests

1. Fork and branch from `main`.
2. Make your change, keep it scoped, and make sure the tests pass.
3. Open a PR describing **what** changed and **why**, and link any related issue.

## License of contributions

Resonode is licensed under **AGPL-3.0**. By contributing, you agree that your
contributions are licensed under the same terms.
