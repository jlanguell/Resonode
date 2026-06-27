"""Query cog — search, summarize, and ask over the server's voice history.

These commands turn stored transcripts into the 'searchable logs' and
'server brain' value props. /search works with no LLM; /summary, /ask use the
configured LLM and fall back gracefully when none is set.
"""

import asyncio
import io

import discord
from discord.ext import commands

from ..transcripts import render_transcript, format_timestamp


class QueryCog(commands.Cog):
    def __init__(self, bot, config, storage, llm, memory):
        self.bot = bot
        self.config = config
        self.storage = storage
        self.llm = llm
        self.memory = memory

    @discord.slash_command(name="transcript", description="Post the latest session's transcript.")
    async def transcript(self, ctx: discord.ApplicationContext):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server.", ephemeral=True)
            return
        sess = self.storage.latest_session(ctx.guild.id)
        if not sess:
            await ctx.respond("No sessions recorded yet. Use `/join` then `/leave`.", ephemeral=True)
            return
        rows = self.storage.session_utterances(sess["id"])
        if not rows:
            await ctx.respond("That session has no transcript text.", ephemeral=True)
            return
        text = render_transcript(rows, (sess.get("guild_name") or "Transcript"))
        await ctx.respond(file=discord.File(io.BytesIO(text.encode("utf-8")),
                                            filename=f"transcript_{sess['id']}.txt"))

    @discord.slash_command(name="search", description="Search this server's voice history.")
    async def search(self, ctx: discord.ApplicationContext,
                     query: discord.Option(str, "Words to search for")):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server.", ephemeral=True)
            return
        words = query.strip()
        if not words:
            await ctx.respond("Please enter something to search for.", ephemeral=True)
            return
        rows = self.storage.search(ctx.guild.id, words, limit=10)
        if not rows:
            await ctx.respond(f"No matches for **{words}**.")
            return
        lines = [f"[{format_timestamp(r['start_s'] or 0)}] {r['speaker_name']}: {r['text']}" for r in rows]
        await ctx.respond("**Matches:**\n" + "\n".join(lines)[:1900])

    @discord.slash_command(name="summary", description="Summarize the latest session (needs an LLM configured).")
    async def summary(self, ctx: discord.ApplicationContext):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server.", ephemeral=True)
            return
        sess = self.storage.latest_session(ctx.guild.id)
        if not sess:
            await ctx.respond("No sessions yet.", ephemeral=True)
            return
        rows = self.storage.session_utterances(sess["id"])
        if not rows:
            await ctx.respond("Nothing to summarize.", ephemeral=True)
            return
        if not getattr(self.llm, "available", False):
            await ctx.respond(self.llm.summarize(""))
            return
        transcript = render_transcript(rows)
        await ctx.defer()
        out = await asyncio.to_thread(self.llm.summarize, transcript)
        await ctx.respond(out[:1900])

    @discord.slash_command(name="ask", description="Ask about this server's voice history.")
    async def ask(self, ctx: discord.ApplicationContext,
                  question: discord.Option(str, "Your question")):
        if ctx.guild is None:
            await ctx.respond("Please use this in a server.", ephemeral=True)
            return
        words = question.strip()
        if not words:
            await ctx.respond("Please enter a question.", ephemeral=True)
            return
        rows = self.memory.recall(ctx.guild.id, words, k=8)
        if not rows:
            await ctx.respond("I don't have anything relevant in memory yet.")
            return
        context = "\n".join(
            f"[{format_timestamp(r['start_s'] or 0)}] {r['speaker_name']}: {r['text']}" for r in rows
        )
        if not getattr(self.llm, "available", False):
            await ctx.respond("**Most relevant lines** (configure an LLM for synthesized answers):\n"
                              + context[:1800])
            return
        await ctx.defer()
        out = await asyncio.to_thread(self.llm.answer, words, context)
        await ctx.respond(out[:1900])
