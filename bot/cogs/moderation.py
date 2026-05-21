import discord
from discord import app_commands
from discord.ext import commands
import datetime
from bot.config import GUILD_OBJ, ACCESS_REQUESTS_CHANNEL_ID
from bot.utils import ch_by_id, now_ts
from bot.ui import AccessRequestView
import aiosqlite
from bot.config import DB_PATH

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Clear chat messages (1..200)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="How many messages to delete (1..200)")
    async def clear_slash(self, interaction: discord.Interaction, amount: int):
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Text channels only.", ephemeral=True)
        amount = max(1, min(amount, 200))
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted: {len(deleted)}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(user="Who to kick", reason="Reason (optional)")
    async def kick_slash(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        await user.kick(reason=reason)
        await interaction.response.send_message(f"✅ Kick: {user.mention}")

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="Who to ban", reason="Reason (optional)")
    async def ban_slash(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        await user.ban(reason=reason, delete_message_days=1)
        await interaction.response.send_message(f"✅ Ban: {user.mention}")

    @app_commands.command(name="unban", description="Unban by user_id")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user_id="User ID")
    async def unban_slash(self, interaction: discord.Interaction, user_id: int):
        g = interaction.guild
        if not g:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        await g.unban(discord.Object(id=user_id))
        await interaction.response.send_message(f"✅ Unban: `{user_id}`")

    @app_commands.command(name="access", description="Submit an access request")
    @app_commands.describe(reason="Text/reason (optional)")
    async def access_slash(self, interaction: discord.Interaction, reason: str = "I want access"):
        g = interaction.guild
        if not g:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        ch = await ch_by_id(self.bot, ACCESS_REQUESTS_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            return await interaction.response.send_message("❌ Management channel not found in config.", ephemeral=True)
        e = discord.Embed(
            title="ACCESS Request",
            description=f"User: {interaction.user.mention}\nReason: {reason}",
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        msg = await ch.send(embed=e, view=AccessRequestView(requester_id=interaction.user.id))
        await interaction.response.send_message("✅ Request sent to the management channel.", ephemeral=True)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO access_requests (guild_id, msg_id, requester_id, created_ts) VALUES (?,?,?,?)",
                (g.id, msg.id, interaction.user.id, now_ts())
            )
            await db.commit()

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(Moderation(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(Moderation(bot))
