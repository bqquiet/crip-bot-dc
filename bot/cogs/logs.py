import discord
from discord.ext import commands

PERMS = {
    "create_instant_invite": "Create Invites",
    "kick_members": "Kick Members",
    "ban_members": "Ban Members",
    "administrator": "Administrator",
    "manage_channels": "Manage Channels",
    "manage_guild": "Manage Server",
    "add_reactions": "Add Reactions",
    "view_audit_log": "View Audit Log",
    "priority_speaker": "Priority Speaker",
    "stream": "Video",
    "read_messages": "View Channels",
    "view_channel": "View Channels",
    "send_messages": "Send Messages",
    "send_tts_messages": "Send TTS Messages",
    "manage_messages": "Manage Messages",
    "embed_links": "Embed Links",
    "attach_files": "Attach Files",
    "read_message_history": "Read Message History",
    "mention_everyone": "Mention @everyone, @here and All Roles",
    "external_emojis": "Use External Emojis",
    "use_external_emojis": "Use External Emojis",
    "view_guild_insights": "View Server Insights",
    "connect": "Connect",
    "speak": "Speak",
    "mute_members": "Mute Members",
    "deafen_members": "Deafen Members",
    "move_members": "Move Members",
    "use_voice_activation": "Use Voice Activity",
    "change_nickname": "Change Nickname",
    "manage_nicknames": "Manage Nicknames",
    "manage_roles": "Manage Roles",
    "manage_webhooks": "Manage Webhooks",
    "manage_emojis": "Manage Emojis and Stickers",
    "manage_emojis_and_stickers": "Manage Emojis and Stickers",
    "use_application_commands": "Use Application Commands",
    "request_to_speak": "Request to Speak",
    "manage_events": "Manage Events",
    "manage_threads": "Manage Threads",
    "create_public_threads": "Create Public Threads",
    "create_private_threads": "Create Private Threads",
    "external_stickers": "Use External Stickers",
    "use_external_stickers": "Use External Stickers",
    "send_messages_in_threads": "Send Messages in Threads",
    "use_embedded_activities": "Use Activities",
    "moderate_members": "Moderate Members (Timeout)",
    "view_creator_monetization_analytics": "View Creator Monetization Analytics",
    "use_soundboard": "Use Soundboard",
    "create_expressions": "Create Expressions (Emojis and Stickers)",
    "create_events": "Create Events",
    "use_external_sounds": "Use External Sounds",
    "send_voice_messages": "Send Voice Messages",
    "send_polls": "Create Polls"
}

class AllLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1451989969412296935

        self.e_edit = "<:edit1:1481209355146887279>"
        self.e_del = "<:delete:1481209323756720159>"
        self.e_add = "<:plus1:1481213731403727050>"
        self.e_rem = "<:minus1:1481213693529161748>"
        self.e_red = "<:edit_red:1481209352231845988>"
        self.e_grn = "<:edit_green:1481209348834197525>"
        self.e_v_join = "<:voice2:1481213768116604980>"
        self.e_v_leave = "<:disconnect:1481209332812091533>"
        self.e_v_move = "<:role_update:1481213741818445945>"
        self.e_ban = "<:ban:1481209289703165983>"
        self.e_unban = "<:unlock:1481213756108177500>"
        self.e_v_off = "<:voice_mute:1481213765641961502>"
        self.e_v_on = "<:voice:1481213764039606376>"

    async def send_log(self, guild, embed):
        ch = guild.get_channel(self.log_channel_id)
        if ch: await ch.send(embed=embed)

    async def get_exec(self, guild, action, target_id=None):
        try:
            async for e in guild.audit_logs(limit=3, action=action):
                if target_id is None or e.target.id == target_id:
                    return e.user
        except: pass
        return None

    def get_ch_type(self, ch):
        if isinstance(ch, discord.TextChannel): return "Text"
        if isinstance(ch, discord.VoiceChannel): return "Voice"
        if isinstance(ch, discord.CategoryChannel): return "Category"
        return "Unknown"

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        emb = discord.Embed(title=f"{self.e_edit} Message Edited", color=0xFFFFFF)
        emb.set_thumbnail(url=before.author.display_avatar.url)
        d = f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n\n"
        d += f"**{self.e_red} Before:**\n`{before.content[:1000] or 'Empty'}`\n\n"
        d += f"**{self.e_grn} After:**\n`{after.content[:1000] or 'Empty'}`\n\n"
        d += f"**Message link:**\n[Go to message]({after.jump_url})"
        emb.description = d
        await self.send_log(before.guild, emb)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        emb = discord.Embed(title=f"{self.e_del} Message Deleted", color=0xED4245)
        emb.set_thumbnail(url=message.author.display_avatar.url)
        d = f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n\n"
        if message.content:
            d += f"**Content:**\n`{message.content[:2000]}`\n\n"
        emb.description = d.strip()
        await self.send_log(message.guild, emb)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            ex = await self.get_exec(before.guild, discord.AuditLogAction.member_update, after.id)
            emb = discord.Embed(title=f"{self.e_edit} Member Updated", color=0xFFFFFF)
            emb.set_thumbnail(url=after.display_avatar.url)
            d = f"**Member:** {after.mention}\n**Edited by:** {ex.mention if ex else 'Unknown'}\n\n"
            d += f"**Changed** `Nickname`\n"
            d += f"{self.e_red} before: `{before.nick or before.name}`\n"
            d += f"{self.e_grn} after: `{after.nick or after.name}`"
            emb.description = d
            await self.send_log(before.guild, emb)

        if before.roles != after.roles:
            added = [r.mention for r in after.roles if r not in before.roles]
            removed = [r.mention for r in before.roles if r not in after.roles]
            ex = await self.get_exec(before.guild, discord.AuditLogAction.member_role_update, after.id)
            
            emb = discord.Embed(title=f"{self.e_edit} Roles Updated", color=0xFFFFFF)
            emb.set_thumbnail(url=after.display_avatar.url)
            d = f"**Member:** {after.mention}\n**Edited by:** {ex.mention if ex else 'Unknown'}\n\n"
            
            if added:
                d += f"{self.e_add} **Roles added:** {', '.join(added)}\n"
            if removed:
                d += f"{self.e_rem} **Roles removed:** {', '.join(removed)}\n"
                
            emb.description = d.strip()
            await self.send_log(before.guild, emb)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.mute != after.mute or before.deaf != after.deaf:
            ex = await self.get_exec(member.guild, discord.AuditLogAction.member_update, member.id)
            emb = discord.Embed(title=f"{self.e_edit} Member Updated", color=0xFFFFFF)
            emb.set_thumbnail(url=member.display_avatar.url)
            d = f"**Member:** {member.mention}\n**Edited by:** {ex.mention if ex else 'Unknown'}\n\n"
            if before.mute != after.mute:
                d += f"**Changed** `Server Mute`\n"
                d += f"{self.e_v_off} muted\n" if after.mute else f"{self.e_v_on} unmuted\n"
            if before.deaf != after.deaf:
                d += f"**Changed** `Server Deafen`\n"
                d += f"{self.e_v_off} deafened\n" if after.deaf else f"{self.e_v_on} undeafened\n"
            emb.description = d.strip()
            await self.send_log(member.guild, emb)

        if before.channel != after.channel:
            if before.channel is None:
                emb = discord.Embed(title=f"{self.e_v_join} Joined Voice Channel", color=0x57F287)
                emb.description = f"**Member:** {member.mention}\n**Channel:** {after.channel.mention}"
            elif after.channel is None:
                emb = discord.Embed(title=f"{self.e_v_leave} Left Voice Channel", color=0xED4245)
                emb.description = f"**Member:** {member.mention}\n**Channel:** {before.channel.mention}"
            else:
                emb = discord.Embed(title=f"{self.e_v_move} Moved Between Voice Channels", color=0xFFFFFF)
                emb.description = f"**Member:** {member.mention}\n**From:** {before.channel.mention}\n**To:** {after.channel.mention}"
            emb.set_thumbnail(url=member.display_avatar.url)
            await self.send_log(member.guild, emb)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        ex = await self.get_exec(role.guild, discord.AuditLogAction.role_create, role.id)
        emb = discord.Embed(title=f"{self.e_add} Role Created", color=0x57F287)
        if ex: emb.set_thumbnail(url=ex.display_avatar.url)
        emb.description = f"**Role:** {role.mention}\n**Created by:** {ex.mention if ex else 'Unknown'}"
        await self.send_log(role.guild, emb)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        ex = await self.get_exec(role.guild, discord.AuditLogAction.role_delete, role.id)
        emb = discord.Embed(title=f"{self.e_del} Role Deleted", color=0xED4245)
        if ex: emb.set_thumbnail(url=ex.display_avatar.url)
        emb.description = f"**Role:** {role.name} ({role.id})\n**Deleted by:** {ex.mention if ex else 'Unknown'}"
        await self.send_log(role.guild, emb)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        ex = await self.get_exec(after.guild, discord.AuditLogAction.role_update, after.id)
        emb = discord.Embed(title=f"{self.e_edit} Role Updated", color=0xFFFFFF)
        if ex: emb.set_thumbnail(url=ex.display_avatar.url)
        d = f"**Role:** {after.mention}\n**Edited by:** {ex.mention if ex else 'Unknown'}\n\n"
        
        chg = []
        if before.name != after.name:
            chg.append(f"**Changed** `Name`\n{self.e_red} before: `{before.name}`\n{self.e_grn} after: `{after.name}`")
        if before.color != after.color:
            chg.append(f"**Changed** `Color`\n{self.e_red} before: `{before.color}`\n{self.e_grn} after: `{after.color}`")
        if before.hoist != after.hoist:
            chg.append(f"**Changed** `Display separately`\n{self.e_red} before: `{'Yes' if before.hoist else 'No'}`\n{self.e_grn} after: `{'Yes' if after.hoist else 'No'}`")
        
        if before.permissions != after.permissions:
            add_p = [p[0] for p in after.permissions if p[1] and not getattr(before.permissions, p[0])]
            rem_p = [p[0] for p in before.permissions if p[1] and not getattr(after.permissions, p[0])]
            if add_p or rem_p:
                pt = "**Changed** `Permissions`\n"
                for p in add_p: 
                    perm_name = PERMS.get(p, p)
                    pt += f"{self.e_add} `{perm_name}` - added\n"
                for p in rem_p: 
                    perm_name = PERMS.get(p, p)
                    pt += f"{self.e_rem} `{perm_name}` - removed\n"
                chg.append(pt.strip())
                
        if chg:
            emb.description = d + "\n\n".join(chg)
            await self.send_log(after.guild, emb)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        ex = await self.get_exec(channel.guild, discord.AuditLogAction.channel_create, channel.id)
        emb = discord.Embed(title=f"{self.e_add} Channel Created", color=0x57F287)
        if ex: emb.set_thumbnail(url=ex.display_avatar.url)
        emb.description = f"**Channel:** {channel.mention}\n**Type:** {self.get_ch_type(channel)}\n**Created by:** {ex.mention if ex else 'Unknown'}"
        await self.send_log(channel.guild, emb)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        ex = await self.get_exec(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
        emb = discord.Embed(title=f"{self.e_del} Channel Deleted", color=0xED4245)
        if ex: emb.set_thumbnail(url=ex.display_avatar.url)
        emb.description = f"**Channel:** {channel.name} ({channel.id})\n**Type:** {self.get_ch_type(channel)}\n**Deleted by:** {ex.mention if ex else 'Unknown'}"
        await self.send_log(channel.guild, emb)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            ex = await self.get_exec(after.guild, discord.AuditLogAction.channel_update, after.id)
            emb = discord.Embed(title=f"{self.e_edit} Channel Updated", color=0xFFFFFF)
            if ex: emb.set_thumbnail(url=ex.display_avatar.url)
            d = f"**Channel:** {after.mention}\n**Type:** {self.get_ch_type(after)}\n**Edited by:** {ex.mention if ex else 'Unknown'}\n\n"
            d += f"**Changed** `Name`\n{self.e_red} before: `{before.name}`\n{self.e_grn} after: `{after.name}`"
            emb.description = d
            await self.send_log(after.guild, emb)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name:
            ex = await self.get_exec(after, discord.AuditLogAction.guild_update)
            emb = discord.Embed(title=f"{self.e_edit} Server Updated", color=0xFFFFFF)
            if ex: emb.set_thumbnail(url=ex.display_avatar.url)
            d = f"**Edited by:** {ex.mention if ex else 'Unknown'}\n\n**Changed** `Server Name`\n"
            d += f"{self.e_red} before: `{before.name}`\n{self.e_grn} after: `{after.name}`"
            emb.description = d
            await self.send_log(after, emb)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        ex = await self.get_exec(guild, discord.AuditLogAction.ban, user.id)
        emb = discord.Embed(title=f"{self.e_ban} Member Banned", color=0x57F287)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.description = f"**Member:** {user.mention}\n**Banned by:** {ex.mention if ex else 'Unknown'}\n\n**Reason:**\n`null`"
        await self.send_log(guild, emb)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        ex = await self.get_exec(guild, discord.AuditLogAction.unban, user.id)
        emb = discord.Embed(title=f"{self.e_unban} Member Unbanned", color=0xED4245)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.description = f"**Member:** {user.mention}\n**Unbanned by:** {ex.mention if ex else 'Unknown'}"
        await self.send_log(guild, emb)

async def setup(bot):
    await bot.add_cog(AllLogs(bot))
