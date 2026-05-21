import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime
from typing import Optional
from bot.config import GUILD_OBJ, EMBED_COLOR_MAIN
from bot.utils import make_embed, set_footer_ru, format_relative_time

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List of available commands")
    async def help_slash(self, interaction: discord.Interaction):
        desc = """Get server info:
`/si` — shows server info (channels, members, boosts, owner, ID).
Get member info:
`/ui [member]` — full info (nickname, device, status, dates, ID).
Get member avatar:
`/ava [member]` — shows avatar.
Get member banner:
`/banner [member]` — shows banner (if set).
Get time info:
`/time [member]` — account age and time on server.
Mini-game "Guess the number":
`/guess [number]` — number from 0 to 9999 (or without argument — generates one)."""
        e = make_embed(title='Available commands:', description=desc, color=EMBED_COLOR_MAIN)
        set_footer_ru(e, interaction, include_user=False, copyright_text='© 2026 bequiet')
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="ava", description="Show avatar")
    @app_commands.describe(user="Member (optional)")
    async def ava_slash(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        member = user or interaction.user
        color = member.color if member.color.value != 0 else EMBED_COLOR_MAIN
        e = discord.Embed(
            title=f"Avatar of: {member}",
            color=color
        )
        avatar_url = member.display_avatar.with_size(512).url
        e.set_image(url=avatar_url)
        e.set_footer(
            text=f"Requested by: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="banner", description="Show banner")
    @app_commands.describe(user="Member (optional)")
    async def banner_slash(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        member = user or interaction.user
        try:
            u = await self.bot.fetch_user(member.id)
        except Exception:
            u = member
        banner = getattr(u, 'banner', None)
        banner_url = banner.with_size(512).url if banner else None
        color = member.color if member.color.value != 0 else EMBED_COLOR_MAIN
        if not banner_url:
            e = discord.Embed(
                title="Member Banner",
                description="❌ This member does not have a banner.",
                color=discord.Color.from_rgb(252, 80, 80)
            )
        else:
            e = discord.Embed(
                title=f"Banner of: {member}",
                color=color
            )
            e.set_image(url=banner_url)
        e.set_footer(
            text=f"Requested by: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="boosters", description="Show active boosters")
    async def boosters_slash(self, interaction: discord.Interaction):
        g = interaction.guild
        if not g:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        boosters = [m for m in g.members if m.premium_since is not None]
        boosters.sort(key=lambda m: m.premium_since or datetime.datetime.now(datetime.timezone.utc))
        e = discord.Embed(color=EMBED_COLOR_MAIN)
        e.set_author(name="Active server boosters:")
        e.set_footer(text="Thanks to them the server gets better!")
        if not boosters:
            e.description = "There are no active boosters on the server at the moment."
        else:
            for i, booster in enumerate(boosters[:25], start=1):
                e.add_field(
                    name=f"#{i} {booster.display_name}",
                    value=booster.name,
                    inline=False
                )
            if len(boosters) > 25:
                e.set_footer(text=f"Thanks to them the server gets better! (Showing 25 of {len(boosters)})")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="guess", description="Mini-game: guess the number")
    @app_commands.describe(number="Your number (0..9999)")
    async def guess_slash(self, interaction: discord.Interaction, number: Optional[int] = None):
        secret = random.randint(1, 9999)
        secret_padded = str(secret).zfill(4)
        e = discord.Embed(color=EMBED_COLOR_MAIN)
        e.set_author(name="Number result:")
        if number is not None:
            number = max(0, min(number, 9999))
            number_padded = str(number).zfill(4)
            your_number_str = f"Your number: {number_padded}"
            if secret_padded == number_padded:
                result_str = f"**Match!** \n{secret_padded} ⭐ **=** ⭐ {number_padded}"
                e.color = discord.Color.from_rgb(133, 219, 25)
            else:
                result_str = f"**No match**: \n{secret_padded} **!=** {number_padded}"
                e.color = discord.Color.from_rgb(255, 83, 31)
            e.description = f"The number was: **{secret_padded}**\n{your_number_str}\n\n{result_str}"
        else:
            e.description = f"The number is: **{secret_padded}**"
        e.set_footer(
            text=f"Requested by: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="si", description="Server info")
    async def si_slash(self, interaction: discord.Interaction):
        g = interaction.guild
        if not g:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)

        total_members = g.member_count
        total_humans = total_bots = online_count = idle_count = dnd_count = offline_count = 0

        for m in g.members:
            if m.bot:
                total_bots += 1
            else:
                total_humans += 1

            status = m.status
            if status == discord.Status.online:
                online_count += 1
            elif status == discord.Status.idle:
                idle_count += 1
            elif status == discord.Status.dnd:
                dnd_count += 1
            else:
                offline_count += 1

        text_channels = sum(1 for ch in g.channels if isinstance(ch, discord.TextChannel))
        voice_channels = sum(1 for ch in g.channels if isinstance(ch, discord.VoiceChannel))
        categories = sum(1 for ch in g.channels if isinstance(ch, discord.CategoryChannel))
        total_channels = text_channels + voice_channels + categories

        verification_level_value = g.verification_level.value
        if verification_level_value == 0:
            verification_level = "None"
        elif verification_level_value == 1:
            verification_level = "Low"
        elif verification_level_value == 2:
            verification_level = "Medium"
        elif verification_level_value == 3:
            verification_level = "High"
        elif verification_level_value >= 4:
            verification_level = "Highest"
        else:
            verification_level = str(g.verification_level)

        e = discord.Embed(color=EMBED_COLOR_MAIN)

        if g.icon:
            e.set_author(name=f"Server Info: {g.name}", icon_url=g.icon.with_size(128).url)
        else:
            e.set_author(name=f"Server Info: {g.name}")

        e.add_field(
            name="Members:",
            value=(
                f"👥 Total: **{total_members}**\n"
                f"👤 Humans: **{total_humans}**\n"
                f"🤖 Bots: **{total_bots}**\n"
                f"🟢 Online: **{online_count + idle_count + dnd_count}**"
            ),
            inline=True
        )

        e.add_field(
            name="Statuses:",
            value=(
                f"🟢 Online: **{online_count}**\n"
                f"🟡 Idle: **{idle_count}**\n"
                f"🔴 Do Not Disturb: **{dnd_count}**\n"
                f"⚫ Offline: **{offline_count}**"
            ),
            inline=True
        )

        e.add_field(
            name="Channels:",
            value=(
                f"📡 Total: **{total_channels}**\n"
                f"💬 Text: **{text_channels}**\n"
                f"🔊 Voice: **{voice_channels}**\n"
                f"📁 Categories: **{categories}**"
            ),
            inline=True
        )

        owner = g.owner or (await g.fetch_member(g.owner_id) if g.owner_id else None)
        e.add_field(
            name="Owner:",
            value=f"👑 {owner.mention}" if owner else "👑 —",
            inline=True
        )

        e.add_field(
            name="Moderation:",
            value=f"🛡️ {verification_level}",
            inline=True
        )

        e.add_field(
            name="Boosts:",
            value=f"🚀 Boosts: **{g.premium_subscription_count}**\n⭐ Level: **{g.premium_tier}**",
            inline=True
        )

        e.add_field(
            name="Server ID:",
            value=f"🔖 `{g.id}`",
            inline=True
        )

        created_at = g.created_at.astimezone(datetime.timezone.utc)
        e.add_field(
            name="Server created:",
            value=f"📅 {created_at.strftime('%d.%m.%Y')}",
            inline=True
        )

        if g.banner:
            e.set_image(url=g.banner.with_size(1024).url)

        e.set_footer(
            text="© 2026 bequiet",
            icon_url="https://cdn.discordapp.com/attachments/861654715745697824/1465834268294123664/Gemini_Generated_Image_6ridj6ridj6ridj6.png?ex=69831dcb&is=6981cc4b&hm=49129df78e334933a166e36ac0bd3dfd4dc437c8b054d40c9fc0505ef10a107f&"
        )

        await interaction.response.send_message(embed=e)

    @app_commands.command(name="ui", description="Member info")
    @app_commands.describe(user="Member (optional)")
    async def ui_slash(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        member = user or interaction.user
        color = member.color if member.color.value != 0 else EMBED_COLOR_MAIN

        e = discord.Embed(color=color)

        e.set_author(
            name=f"Member Info: {member.name}",
            icon_url=member.display_avatar.with_size(128).url
        )

        e.description = "**General:**\n** **"

        tag = member.name if member.discriminator == '0' else f"{member.name}#{member.discriminator}"
        e.add_field(name="Username:", value=f"👤 {tag}", inline=True)

        device = "❓ Unknown"
        if member.voice and member.voice.channel:
            device = "🖥️ Desktop"
        elif member.activities:
            device = "🎮 Active"
        elif member.status != discord.Status.offline:
            device = "🖥️ Desktop"
        e.add_field(name="Device:", value=device, inline=True)

        if member.status == discord.Status.online:
            status_text = "🟢 Online"
        elif member.status == discord.Status.idle:
            status_text = "🟡 Idle"
        elif member.status == discord.Status.dnd:
            status_text = "🔴 Do Not Disturb"
        elif member.status == discord.Status.offline:
            status_text = "⚫ Offline"
        else:
            status_text = "❓ Unknown"

        e.add_field(name="Status:", value=status_text, inline=True)

        if member.global_name and member.global_name != member.name:
            e.add_field(name="Display Name:", value=f"🧑‍💼 {member.global_name}", inline=True)

        if member.nick:
            e.add_field(name="Server Nickname:", value=f"📛 {member.nick}", inline=True)

        top_role = member.top_role if member.top_role and member.top_role.name != '@everyone' else None
        e.add_field(name="Top Role:", value=top_role.mention if top_role else "—", inline=False)

        joined_ts = int(member.joined_at.timestamp()) if member.joined_at else 0
        e.add_field(
            name="Joined:",
            value=f"<t:{joined_ts}:d>\n⏱️ (<t:{joined_ts}:R>)" if joined_ts else "—",
            inline=True
        )

        created_ts = int(member.created_at.timestamp())
        e.add_field(
            name="Registered:",
            value=f"<t:{created_ts}:d>\n📅 (<t:{created_ts}:R>)",
            inline=True
        )

        e.add_field(name="ID:", value=f"🆔 `{member.id}`", inline=False)

        try:
            u = await self.bot.fetch_user(member.id)
            flags = getattr(u, 'public_flags', None)
        except:
            flags = None

        badges = []
        if flags:
            if flags.staff: badges.append("🛡️")
            if flags.partner: badges.append("🤝")
            if flags.hypesquad: badges.append("🎉")
            if flags.bug_hunter: badges.append("🐛")
            if flags.hypesquad_bravery: badges.append("🦁")
            if flags.hypesquad_brilliance: badges.append("🦄")
            if flags.hypesquad_balance: badges.append("🌙")
            if flags.early_supporter: badges.append("💎")
            if flags.verified_bot_developer: badges.append("👨‍💻")
            if flags.active_developer: badges.append("🔧")

        if hasattr(member, 'premium_since') and member.premium_since:
            badges.append("✨")
        if member.bot:
            badges.append("🤖")

        if badges:
            e.add_field(name="Badges:", value=" ".join(badges), inline=False)

        custom_status = None
        game = None

        for activity in member.activities:
            if activity.type == discord.ActivityType.custom and activity.name:
                custom_status = activity
                break
            elif activity.type == discord.ActivityType.playing:
                game = activity

        if custom_status:
            status_text = custom_status.name or "—"
            if custom_status.emoji:
                status_text = f"{custom_status.emoji} {status_text}"
            e.add_field(name="Custom Status:", value=status_text, inline=False)
        elif game:
            e.add_field(name="Playing:", value=f"🎮 {game.name}", inline=False)

        try:
            u = await self.bot.fetch_user(member.id)
            if getattr(u, 'banner', None):
                e.set_image(url=u.banner.with_size(1024).url)
        except:
            pass

        e.set_footer(
            text=f"Requested by: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=e)

    @app_commands.command(name="time", description="Account age and time on server")
    @app_commands.describe(user="Member (optional)")
    async def time_slash(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        member = user or interaction.user
        now = datetime.datetime.now(datetime.timezone.utc)
        acc_age = now - member.created_at
        join_age = (now - member.joined_at) if member.joined_at else None
        e = discord.Embed(color=EMBED_COLOR_MAIN)
        e.set_author(
            name=f"Member Info: {member.name}",
            icon_url=member.display_avatar.with_size(128).url
        )
        e.add_field(
            name="Account age:",
            value=format_relative_time(acc_age),
            inline=True
        )
        if join_age:
            e.add_field(
                name="Time on server:",
                value=format_relative_time(join_age),
                inline=False
            )
        else:
            e.add_field(
                name="Time on server:",
                value="—",
                inline=False
            )
        e.set_footer(
            text=f"Requested by: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=e)

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(General(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(General(bot))
