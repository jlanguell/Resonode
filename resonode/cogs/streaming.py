"""Live transcription cog — /join, /leave that stream lines as people speak.

Loaded instead of RecordingCog when RESONODE_STREAMING=true. Each finished
utterance is transcribed and posted live, and persisted so !search/!ask work on
streamed sessions too. A full transcript file is posted when the session ends.
"""
from __future__ import annotations

import asyncio
import io
import time
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands

from ..storage import Utterance
from ..streaming import make_streaming_sink, STREAM_RATE, STREAM_CHANNELS, STREAM_WIDTH
from ..transcripts import render_transcript, format_timestamp

IDLE_FLUSH_MS = 700      # flush a speaker's buffer this long after they go quiet
WATCHDOG_INTERVAL = 0.4  # seconds between idle checks


class StreamingCog(commands.Cog):
    def __init__(self, bot, config, stt, storage):
        self.bot = bot
        self.config = config
        self.stt = stt
        self.storage = storage
        self.sessions: dict[int, dict] = {}
        self.tx_dir = Path(config.transcripts_dir)
        self.tx_dir.mkdir(parents=True, exist_ok=True)

    @discord.slash_command(name="join", description="Join your voice channel and transcribe live.")
    async def join(self, ctx: discord.ApplicationContext):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server voice channel.", ephemeral=True)
            return
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.respond("You need to be in a voice channel first.", ephemeral=True)
            return
        if ctx.guild.id in self.sessions:
            await ctx.respond("I'm already live in this server. Use `/leave` to stop.", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        await ctx.defer()
        try:
            vc = await channel.connect()
        except discord.ClientException:
            await ctx.respond("I'm already connected to a voice channel here.")
            return

        loop = asyncio.get_running_loop()
        session_id = self.storage.start_session(
            ctx.guild.id, ctx.guild.name, channel.id, channel.name, self.config.whisper_model
        )
        queue: asyncio.Queue = asyncio.Queue()

        def on_utterance(uid: int, pcm: bytes):  # decode thread -> loop
            loop.call_soon_threadsafe(queue.put_nowait, (uid, pcm))

        sink = make_streaming_sink(on_utterance)
        state = {
            "vc": vc, "sink": sink, "session_id": session_id,
            "channel": ctx.channel, "guild": ctx.guild,
            "start": time.monotonic(), "queue": queue,
        }
        self.sessions[ctx.guild.id] = state
        vc.start_recording(sink, self._on_finish, ctx.channel)
        state["consumer"] = asyncio.create_task(self._consume(ctx.guild.id))
        state["watchdog"] = asyncio.create_task(self._watchdog(ctx.guild.id))
        await ctx.respond(
            f"🔴 **Live transcription** started for **{channel.name}** — lines appear here "
            f"as people speak. `/leave` to stop."
        )

    @discord.slash_command(name="leave", description="Stop live transcription and post the full transcript.")
    async def leave(self, ctx: discord.ApplicationContext):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server.", ephemeral=True)
            return
        if ctx.guild.id not in self.sessions:
            await ctx.respond("I'm not live right now.", ephemeral=True)
            return
        await ctx.respond("Stopping live transcription…")
        self.sessions[ctx.guild.id]["vc"].stop_recording()  # triggers _on_finish

    @discord.slash_command(name="ping", description="Check that the bot is responsive.")
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! ({round(self.bot.latency * 1000)}ms)")

    def _speaker_name(self, guild, uid):
        member = guild.get_member(uid)
        if member is not None:
            return member.display_name
        user = self.bot.get_user(uid)
        return user.display_name if user is not None else f"User {uid}"

    async def _transcribe_and_emit(self, state, uid, pcm):
        try:
            segs = await self.stt.transcribe_pcm(pcm, STREAM_RATE, STREAM_CHANNELS, STREAM_WIDTH)
        except Exception as exc:
            print(f"[resonode] streaming STT error: {exc}")
            return
        text = " ".join(s.text for s in segs).strip()
        if not text:
            return
        name = self._speaker_name(state["guild"], uid)
        t = time.monotonic() - state["start"]
        try:
            self.storage.add_utterance(
                state["session_id"], state["guild"].id,
                Utterance(speaker_name=name, speaker_id=uid, start_s=t, end_s=t,
                          text=text, lang=(segs[0].lang if segs else None)),
            )
        except Exception:
            pass
        try:
            await state["channel"].send(f"`[{format_timestamp(t)}]` **{name}:** {text}")
        except Exception:
            pass

    async def _consume(self, guild_id):
        state = self.sessions.get(guild_id)
        if not state:
            return
        q = state["queue"]
        try:
            while True:
                uid, pcm = await q.get()
                await self._transcribe_and_emit(state, uid, pcm)
        except asyncio.CancelledError:
            pass

    async def _watchdog(self, guild_id):
        try:
            while guild_id in self.sessions:
                await asyncio.sleep(WATCHDOG_INTERVAL)
                state = self.sessions.get(guild_id)
                if not state:
                    break
                for uid, pcm in state["sink"].flush_idle(IDLE_FLUSH_MS):
                    state["queue"].put_nowait((uid, pcm))
        except asyncio.CancelledError:
            pass

    async def _on_finish(self, sink, channel):
        guild = channel.guild
        state = self.sessions.get(guild.id)
        try:
            await sink.vc.disconnect()
        except Exception:
            pass
        if not state:
            return
        for key in ("watchdog", "consumer"):
            task = state.get(key)
            if task:
                task.cancel()
        q = state["queue"]
        while not q.empty():
            uid, pcm = q.get_nowait()
            await self._transcribe_and_emit(state, uid, pcm)
        for uid, pcm in sink.flush_all():
            await self._transcribe_and_emit(state, uid, pcm)

        self.storage.end_session(state["session_id"])
        rows = self.storage.session_utterances(state["session_id"])
        self.sessions.pop(guild.id, None)
        if not rows:
            await channel.send("Live session ended — no speech was transcribed.")
            return
        header = (
            f"Live transcript for {guild.name}\n"
            f"Recorded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Model: {self.config.whisper_model}\n" + "=" * 60
        )
        text = render_transcript(rows, header)
        await channel.send(
            content="Live session ended. Full transcript:",
            file=discord.File(io.BytesIO(text.encode("utf-8")),
                              filename=f"transcript_{state['session_id']}.txt"),
        )
