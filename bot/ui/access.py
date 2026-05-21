import discord
import datetime
from bot.config import IMM_ROLE_ID
from bot.utils import send_chronology, send_modlog

class AccessRequestView(discord.ui.View):
    def __init__(self, requester_id: int):
        super().__init__(timeout=None)
        self.requester_id = requester_id

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔘", custom_id="access:approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Error.", ephemeral=True)

        if not interaction.user.guild_permissions.manage_guild and not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("No permission.", ephemeral=True)

        member = interaction.guild.get_member(self.requester_id)
        if not member:
            return await interaction.response.send_message("User not found.", ephemeral=True)

        role = interaction.guild.get_role(IMM_ROLE_ID)
        if role and role not in member.roles:
            await member.add_roles(role, reason="Access approved")

        await interaction.response.send_message(f"✅ Approved: {member.mention}", ephemeral=True)

        emb = discord.Embed(
            title="ACCESS: Approved",
            description=f"Request: <@{self.requester_id}>\nModerator: {interaction.user.mention}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_chronology(interaction.client, emb)
        await send_modlog(interaction.client, emb)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔘", custom_id="access:decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Error.", ephemeral=True)

        if not interaction.user.guild_permissions.manage_guild and not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("No permission.", ephemeral=True)

        await interaction.response.send_message(f"❌ Declined: <@{self.requester_id}>", ephemeral=True)

        emb = discord.Embed(
            title="ACCESS: Declined",
            description=f"Request: <@{self.requester_id}>\nModerator: {interaction.user.mention}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_chronology(interaction.client, emb)
        await send_modlog(interaction.client, emb)
