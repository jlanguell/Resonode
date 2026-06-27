# Security Policy

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Resonode handles voice data and a Discord bot token, so security and privacy
issues are taken seriously. To report one privately:

- Use **[GitHub private vulnerability reporting](https://github.com/jlanguell/resonode/security/advisories/new)**
  (the repo's **Security** tab → **Report a vulnerability**), or
- if that isn't available, open a minimal public issue that says only
  *"security — please open a private channel"* (no details), and a maintainer
  will follow up privately.

Please include, as best you can: what the issue is, steps to reproduce, the
impact, and any suggested fix. We aim to acknowledge reports within a few days.

## Supported versions

Resonode is pre-1.0 and ships from `main`. Security fixes land on `main`; please
test against the latest commit before reporting.

## Handling secrets

Resonode never stores your bot token in the repository — it lives only in `.env`,
which is gitignored. If a token is ever exposed, **reset it immediately** in the
Discord Developer Portal (**Bot → Reset Token**). Never commit `.env`,
`recordings/`, or `transcripts/`.
