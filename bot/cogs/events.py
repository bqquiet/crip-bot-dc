import discord
from discord.ext import commands
import datetime
import random
from bot.config import (
    GUILD_ID, RAID_TIME_WINDOW, RAID_JOIN_LIMIT, RAID_TIMEOUT_SECONDS,
    IMM_ROLE_ID, SPAM_TIME_WINDOW, SPAM_MSG_LIMIT, AUTOMUTE_SECONDS,
    XP_COOLDOWN_SECONDS, TEMPVOICE_CREATE_CHANNEL_ID, TEMPVOICE_CATEGORY_ID
)
from bot.utils import now_ts, timeout_member, send_modlog, send_chronology, mention, dt_ru
from bot.database import process_message_xp, tv_get_owner, tv_delete, tv_set

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_buckets = []
        self.msg_buckets = {}

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(status=discord.Status.dnd)
        print(f"Logged in as {self.bot.user}")
        emb = discord.Embed(title="Bot Ready", description=f"Started: `{dt_ru()}`", timestamp=datetime.datetime.now(datetime.timezone.utc))
        await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        self.join_buckets.append(now_ts())
        cutoff = now_ts() - RAID_TIME_WINDOW
        while self.join_buckets and self.join_buckets[0] < cutoff:
            self.join_buckets.pop(0)
        if len(self.join_buckets) >= RAID_JOIN_LIMIT:
            await timeout_member(member, RAID_TIMEOUT_SECONDS, "Anti-raid: join spike")
            emb = discord.Embed(
                title="Anti-Raid",
                description=f"Timed out {member.mention} for {RAID_TIMEOUT_SECONDS}s (join spike)",
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await send_modlog(self.bot, emb)
            await send_chronology(self.bot, emb)

        role = member.guild.get_role(IMM_ROLE_ID)
        if role:
            try:
                await member.add_roles(role, reason="Auto role on join (IMM)")
            except:
                pass

        emb = discord.Embed(
            title="Member Join",
            description=f"Joined: {mention(member)}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        emb = discord.Embed(
            title="Member Leave",
            description=f"Left: `{member}` (`{member.id}`)",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.guild.id != GUILD_ID:
            return
            
        uid = message.author.id
        self.msg_buckets.setdefault(uid, [])
        self.msg_buckets[uid].append(now_ts())
        cutoff = now_ts() - SPAM_TIME_WINDOW
        self.msg_buckets[uid] = [t for t in self.msg_buckets[uid] if t >= cutoff]

        if len(self.msg_buckets[uid]) >= SPAM_MSG_LIMIT:
            if isinstance(message.author, discord.Member):
                await timeout_member(message.author, AUTOMUTE_SECONDS, "Anti-spam automute")
                emb = discord.Embed(
                    title="Anti-Spam",
                    description=f"Timed out {message.author.mention} for {AUTOMUTE_SECONDS}s (spam)",
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                await send_modlog(self.bot, emb)
            try:
                await message.channel.send(f"⚠️ {message.author.mention} anti-spam: timeout.", delete_after=8)
            except:
                pass

        await process_message_xp(message.guild.id, uid, XP_COOLDOWN_SECONDS)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.guild.id != GUILD_ID:
            return
        if message.author and message.author.bot:
            return
        emb = discord.Embed(
            title="Message Deleted",
            description=f"Author: {message.author.mention if message.author else '—'}\nChannel: {message.channel.mention}\nContent: {message.content[:800] if message.content else '(empty)'}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or after.guild.id != GUILD_ID:
            return
        if after.author and after.author.bot:
            return
        if before.content == after.content:
            return
        emb = discord.Embed(
            title="Message Edited",
            description=f"Author: {after.author.mention}\nChannel: {after.channel.mention}\nBefore: {before.content[:500]}\nAfter: {after.content[:500]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild.id != GUILD_ID:
            return
        if before.timed_out_until != after.timed_out_until:
            emb = discord.Embed(
                title="Timeout Update",
                description=f"{after.mention}\nBefore: {before.timed_out_until}\nAfter: {after.timed_out_until}",
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await send_modlog(self.bot, emb)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.guild.id != GUILD_ID:
            return
        if after.channel and isinstance(after.channel, discord.VoiceChannel) and after.channel.id == TEMPVOICE_CREATE_CHANNEL_ID:
            category = member.guild.get_channel(TEMPVOICE_CATEGORY_ID)
            if not isinstance(category, discord.CategoryChannel):
                return
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True, move_members=True, mute_members=True)
            }
            name = f"🔒 {member.display_name}"
            vc = await member.guild.create_voice_channel(
                name=name[:80],
                category=category,
                overwrites=overwrites,
                user_limit=0,
                reason="TempVoice create"
            )
            await tv_set(member.guild.id, member.id, vc.id)

            await member.move_to(vc, reason="Move to TempVoice")

            emb = discord.Embed(
                title="TempVoice Created",
                description=f"Owner: {member.mention}\nChannel: **{vc.name}** (`{vc.id}`)",
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await send_modlog(self.bot, emb)

        if before.channel and isinstance(before.channel, discord.VoiceChannel):
            owner_id = await tv_get_owner(member.guild.id, before.channel.id)
            if owner_id and len(before.channel.members) == 0:
                await tv_delete(member.guild.id, before.channel.id)
                try:
                    await before.channel.delete(reason="TempVoice auto-delete (empty)")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Events(bot))
