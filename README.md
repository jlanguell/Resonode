# Resonode

**Real-time voice AI + memory for Discord.**

Resonode listens in your voice channels, turns speech into searchable text and
action *as it happens*, and **remembers** it — a persistent "server brain" so
your community never loses a decision, an action item, or who said what.

> **Status — building in public.** The local transcription core works **today**
> (join a voice channel, get a speaker-attributed transcript). The real-time and
> memory features below are the roadmap, shipping incrementally. See
> [Status & roadmap](#status--roadmap).

`Listens · Remembers · Acts`

---

## The problem

Communities live in voice — but voice is a black hole. Nothing said out loud is
searchable, captioned, translated, moderated, or remembered. Meeting notes
evaporate, newcomers can't catch up, deaf and hard-of-hearing members are left
out, moderators can't see what happens in VC, and the next day nobody can recall
what was actually decided.

Almost no bots fix this, for one reason: **doing real-time voice on Discord is
genuinely hard.** Voice *receive* — capturing and processing live audio — is
famously underdocumented, so the whole ecosystem (MEE6, Carl-bot, ProBot, and
friends) is text-only. Resonode is built on that hard capability and turns it
into product.

## What Resonode does

**Real-time voice**

- **Live transcription → action** — meeting-style transcripts as people speak, not after.
- **Accessibility captions** — live captions so every member can follow along.
- **Live translation** — speak in one language, read in another, in real time.
- **Speaker diarization** — every line attributed to who actually said it.
- **Searchable voice logs** — every session saved, indexed, and searchable.
- **AI voice moderation** — flag harmful speech in voice, not just in text.

**The server brain (memory)**

- **Persistent memory** — remembers decisions, action items, and member context across sessions.
- **RAG over voice + text** — ask *"what did we decide about the launch?"* and get an answer with citations from your own history.
- **A queryable community mind** — the long-term memory voice agents normally lack, because people can't scroll back through a conversation they had out loud.

## Why this is the moat

The capability barrier *is* the opportunity. Streaming speech-to-text and LLMs
went cheap and commoditized in the last year — but **voice receive is still the
hard part**, and the incumbents are text-first. A bot that already solves
real-time voice, then layers durable memory on top, owns a niche the big players
structurally avoid.

## How it works

```
Discord voice receive
        │  live audio, per speaker
        ▼
Streaming STT   (Whisper / Deepgram)
        │  text + timestamps
        ▼
LLM layer       (summarize · diarize · translate · moderate)
        │  structured events
        ▼
Memory          (vector store + RAG: pgvector / Qdrant)
        │
        ▼
Actions    →    post · caption · translate · flag · recall
```

Today's local transcription core is the first link in that chain; each stage
above is being built out toward streaming and memory.

## Status & roadmap

**Live today**

- Joins a voice channel on command, records the session, and posts a
  **speaker-attributed, timestamped transcript**.
- Transcription runs **locally** with
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — no API key, no
  cost, and audio never leaves your machine.

**In progress**

- [x] Real-time **streaming** transcription *(prototype)* — enable with `RESONODE_STREAMING=true`; live captions next
- [ ] True **speaker diarization** (beyond Discord's per-speaker streams)
- [ ] **Live translation**
- [ ] **AI voice moderation**
- [ ] Persistent **RAG "server brain"** memory over voice + text history
- [ ] **Searchable** dashboard for logs and recall
- [ ] **Discord App Directory** listing + Premium App subscription tier

## Commands

| Command  | What it does                                                     |
| -------- | --------------------------------------------------------------- |
| `/join`  | Joins the voice channel **you're** in and starts recording.     |
| `/leave` | Leaves, transcribes the session, and posts the transcript file. |
| `/ping`  | Quick "is the bot alive?" check.                                |

*(Captions, translate, and ask/recall commands arrive with the features above.)*

Each transcript line looks like:

```
[00:00:04] Alice: Hey, can everyone hear me?
[00:00:07] Bob: Yep, loud and clear.
```

> **Ordering note:** Discord delivers one audio stream per speaker, so the
> running order is reconstructed from Whisper's timestamps. Each line is
> correctly attributed; interleaving between speakers can be slightly approximate
> (true diarization is on the roadmap).

---

## Quickstart

### 1. Create the bot in Discord

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. Open the **Bot** tab → **Add Bot**, then **Reset Token** and copy it.
3. *No privileged intents are required* — Resonode uses **slash commands**, so
   you do **not** need to enable the Message Content Intent.
4. Open **OAuth2 → URL Generator**:
   - **Scopes:** `bot` and `applications.commands`
   - **Bot Permissions:** `View Channels`, `Send Messages`, `Attach Files`, `Connect`, `Speak`
   - Open the generated URL and invite the bot to your server.

### 2. Configure

From this folder (`Resonode`):

```powershell
copy .env.example .env
notepad .env
```

Set `DISCORD_TOKEN` to your token. You can also change `WHISPER_MODEL` (see
[Model sizes](#model-sizes)).

### 3. Install & run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py        # or just double-click start.bat
```

First launch downloads the Whisper model (~150 MB for `base`) and prints
`Resonode online as ...` when ready. Then: join a voice channel, run `/join`,
talk, and run `/leave` to get the transcript. (Global slash commands can take up
to ~1 hour to appear the first time — set `RESONODE_DEV_GUILD` to your server's
ID in `.env` for instant registration while testing.)

## Model sizes

Set `WHISPER_MODEL` in `.env`. Larger = more accurate but slower / more RAM.

| Model      | Approx. size | Notes                                     |
| ---------- | ------------ | ----------------------------------------- |
| `tiny`     | ~75 MB       | Fastest, least accurate                   |
| `base`     | ~150 MB      | Good default for casual use **(default)** |
| `small`    | ~480 MB      | Noticeably better accuracy                |
| `medium`   | ~1.5 GB      | Strong accuracy, slower on CPU            |
| `large-v3` | ~3 GB        | Best accuracy, slow without a GPU         |

**GPU:** with an NVIDIA GPU (CUDA + cuDNN), set `WHISPER_DEVICE=cuda` in `.env`
for much faster transcription.

## Privacy & consent

Voice is sensitive, and a tool that records **and remembers** it raises the
stakes. Only capture voice with everyone's knowledge and consent, follow your
local laws on recording, and be clear with your community about what is stored
and for how long. The current build keeps everything **local**; any hosted or
memory features will ship with explicit, opt-in controls.

- **One recording per server** at a time; re-running `/join` while already
  recording is ignored. Multiple servers at once is fine.
- **No ffmpeg needed** — faster-whisper reads audio via its bundled backend (PyAV).
- Temporary per-speaker WAVs are written to `recordings/` during transcription
  and deleted automatically afterward.

## Brand assets

Resonode's identity — the **voice-core + memory-constellation** mark — lives in
`assets/resonode/`. Everything is 100% procedural and original (no stock art, no
Discord logo), free to use and modify:

- `resonode_app_icon_1024.png` (+ `_512`) — bot **avatar** / app icon
- `resonode_banner.png` (1600×900) — profile / **App Directory** banner
- `resonode_banner_680x240.png` — compact banner
- Four colourways — **neural** (default), **plasma**, **teal·gold**, **blurple** — for the icon and banners
- `resonode_overview_concepts.png`, `resonode_overview_palettes.png` — selection boards
- `RESONODE_visual_language.md` — the design system

Set the avatar under **Bot → Profile** and the cover image under **General
Information** in the Developer Portal.

## Deploy

Open-source core for reputation, plus a paid hosted tier. Distribute through the
**Discord App Directory** with native **Premium Apps** (guild subscriptions;
~$5–15/mo is the going benchmark for comparable bots).

## Project layout

```
bot.py               # the bot — voice receive + transcription (Resonode core)
requirements.txt     # Python dependencies
.env.example         # copy to .env and add your token
start.bat            # convenience launcher (Windows)
assets/resonode/     # Resonode brand kit (icons, banners, boards, design system)
transcripts/         # finished transcripts land here
recordings/          # temp audio during transcription (auto-cleaned)
```
