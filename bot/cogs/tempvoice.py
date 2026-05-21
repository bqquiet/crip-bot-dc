import discord
from discord import app_commands
from discord.ext import commands
import os
from bot.config import GUILD_OBJ, TEMPVOICE_UI_IMAGE
from bot.utils import make_embed, is_tv_owner
from bot.database import tv_set
from bot.ui import TempVoicePanel

class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voicepanel", description="Send the temporary voice channel panel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def voicepanel_slash(self, interaction: discord.Interaction):
        e = make_embed(
            title="TempVoice Interface",
            description=(
                "Use this interface to manage your temporary voice channels.\n"
                "More options are available via /voice commands."
            )
        )
        try:
            if os.path.exists(TEMPVOICE_UI_IMAGE):
                filename = os.path.basename(TEMPVOICE_UI_IMAGE)
                file = discord.File(TEMPVOICE_UI_IMAGE, filename=filename)
                e.set_image(url=f"attachment://{filename}")
                await interaction.response.send_message(embed=e, view=TempVoicePanel(), file=file)
                return
        except Exception:
            pass
        await interaction.response.send_message(embed=e, view=TempVoicePanel())

    voice_group = app_commands.Group(name="voice", description="Temporary voice channel commands")

    @voice_group.command(name="name", description="Change the name of your private voice channel")
    @app_commands.describe(new_name="New name")
    async def voice_name(self, interaction: discord.Interaction, new_name: str):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        await vc.edit(name=new_name[:80], reason="TempVoice rename")
        await interaction.response.send_message("✅ Name changed.", ephemeral=True)

    @voice_group.command(name="limit", description="Change user limit")
    @app_commands.describe(value="0..99")
    async def voice_limit(self, interaction: discord.Interaction, value: int):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        value = max(0, min(value, 99))
        await vc.edit(user_limit=value, reason="TempVoice limit")
        await interaction.response.send_message("✅ Limit changed.", ephemeral=True)

    @voice_group.command(name="lock", description="Lock access (default role connect=False)")
    async def voice_lock(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        ow = vc.overwrites_for(interaction.guild.default_role)
        ow.connect = False
        await vc.set_permissions(interaction.guild.default_role, overwrite=ow, reason="TempVoice lock")
        await interaction.response.send_message("✅ Channel locked.", ephemeral=True)

    @voice_group.command(name="unlock", description="Unlock access (default role connect=None)")
    async def voice_unlock(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        ow = vc.overwrites_for(interaction.guild.default_role)
        ow.connect = None
        await vc.set_permissions(interaction.guild.default_role, overwrite=ow, reason="TempVoice unlock")
        await interaction.response.send_message("✅ Channel unlocked.", ephemeral=True)

    @voice_group.command(name="region", description="Change the voice channel region (RTC)")
    @app_commands.describe(value="auto/europe/us-east/us-west")
    async def voice_region(self, interaction: discord.Interaction, value: str):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        value = value.lower().strip()
        allowed = {
            "auto": None,
            "europe": "europe",
            "us-east": "us-east",
            "us-west": "us-west",
        }
        if value not in allowed:
            return await interaction.response.send_message("❌ Available: auto, europe, us-east, us-west", ephemeral=True)
        await vc.edit(rtc_region=allowed[value], reason="TempVoice region change")
        await interaction.response.send_message(f"✅ Region changed: **{value}**", ephemeral=True)

    @voice_group.command(name="invite", description="Grant access to a user")
    @app_commands.describe(user="User")
    async def voice_invite(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        ow = vc.overwrites_for(user)
        ow.connect = True
        ow.view_channel = True
        await vc.set_permissions(user, overwrite=ow, reason="TempVoice invite")
        await interaction.response.send_message(f"✅ Access granted: {user.mention}", ephemeral=True)

    @voice_group.command(name="kick", description="Kick a user from the channel")
    @app_commands.describe(user="User")
    async def voice_kick(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        if user.voice and user.voice.channel and user.voice.channel.id == vc.id:
            await user.move_to(None, reason="TempVoice kick")
            await interaction.response.send_message(f"✅ Kicked: {user.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("They are not in your channel.", ephemeral=True)

    @voice_group.command(name="ban", description="Ban from channel (deny connect/view)")
    @app_commands.describe(user="User")
    async def voice_ban(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        ow = vc.overwrites_for(user)
        ow.connect = False
        ow.view_channel = False
        await vc.set_permissions(user, overwrite=ow, reason="TempVoice ban")

        if user.voice and user.voice.channel and user.voice.channel.id == vc.id:
            await user.move_to(None, reason="TempVoice ban")

        await interaction.response.send_message(f"✅ Banned from channel: {user.mention}", ephemeral=True)

    @voice_group.command(name="unban", description="Unban from channel (remove overwrite)")
    @app_commands.describe(user="User")
    async def voice_unban(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        await vc.set_permissions(user, overwrite=None, reason="TempVoice unban")
        await interaction.response.send_message(f"✅ Unbanned: {user.mention}", ephemeral=True)

    @voice_group.command(name="trust", description="Add trust (internal list)")
    @app_commands.describe(user="User")
    async def voice_trust(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        await interaction.response.send_message(f"✅ Trust granted: {user.mention}", ephemeral=True)

    @voice_group.command(name="untrust", description="Remove trust (internal list)")
    @app_commands.describe(user="User")
    async def voice_untrust(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        await interaction.response.send_message(f"✅ Trust removed: {user.mention}", ephemeral=True)

    @voice_group.command(name="transfer", description="Transfer channel ownership")
    @app_commands.describe(user="User (must be in your voice channel)")
    async def voice_transfer(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join your private voice channel first.", ephemeral=True)
        if not await is_tv_owner(interaction.user, vc):
            return await interaction.response.send_message("You are not the owner.", ephemeral=True)
        if not (user.voice and user.voice.channel and user.voice.channel.id == vc.id):
            return await interaction.response.send_message("The user must be in your voice channel.", ephemeral=True)
        await tv_set(interaction.guild.id, user.id, vc.id)
        await interaction.response.send_message(f"✅ Ownership transferred: {user.mention}", ephemeral=True)

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(TempVoice(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(TempVoice(bot))
