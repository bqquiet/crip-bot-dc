import discord
from discord import app_commands
from discord.ext import commands
import datetime
from bot.config import GUILD_OBJ, REPORT_ROLES, VOTING_ROLES
from bot.ui import RankVoteView
from bot.database import create_vote
from bot.utils import send_chronology

class Voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rangup", description="Request a rank promotion")
    @app_commands.describe(target="Name | ID | Real player name")
    async def rangup_slash(self, interaction: discord.Interaction, target: str):
        await self.handle_rank_proposal(interaction, target, "Rank Promotion", "rangup")

    @app_commands.command(name="rangdown", description="Request a rank demotion")
    @app_commands.describe(target="Name | ID | Real player name")
    async def rangdown_slash(self, interaction: discord.Interaction, target: str):
        await self.handle_rank_proposal(interaction, target, "Rank Demotion", "rangdown")

    @app_commands.command(name="famwarn", description="Request to issue a warning")
    @app_commands.describe(target="Name | ID | Real player name")
    async def famwarn_slash(self, interaction: discord.Interaction, target: str):
        await self.handle_rank_proposal(interaction, target, "Issue Warning", "famwarn")

    @app_commands.command(name="famkick", description="Request to kick from family")
    @app_commands.describe(target="Name | ID | Real player name")
    async def famkick_slash(self, interaction: discord.Interaction, target: str):
        await self.handle_rank_proposal(interaction, target, "Family Kick", "famkick")

    async def handle_rank_proposal(self, interaction: discord.Interaction, target: str, action_type: str, command_type: str):
        if not any(role.id in REPORT_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message("❌ You don't have permission to create requests!", ephemeral=True)

        voting_channel_id = 1469278285128269919
        voting_channel = self.bot.get_channel(voting_channel_id)
        if not voting_channel:
            return await interaction.response.send_message("❌ Voting channel not found!", ephemeral=True)

        if command_type == 'rangup':
            color = discord.Color.from_rgb(50, 150, 50)
        elif command_type == 'rangdown':
            color = discord.Color.from_rgb(200, 150, 50)
        elif command_type == 'famwarn':
            color = discord.Color.from_rgb(255, 200, 50)
        else:
            color = discord.Color.from_rgb(200, 50, 50)

        e = discord.Embed(
            title=f"🗳️ New vote: {action_type}",
            description=(
                f"**Target:** {target}\n\n"
                f"📊 **Results:**\n"
                f"✅ For: **0**\n"
                f"❌ Against: **0**\n"
                f"👥 Voted: **0/4**\n\n"
                f"👥 **Voters:**\n—"
            ),
            color=color
        )
        e.set_footer(text=f"Requested by: {interaction.user.name} | ID: {interaction.user.id} • ⏳ Active")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in VOTING_ROLES if interaction.guild.get_role(rid)])

        view = RankVoteView(0, target, action_type, command_type, interaction.user.id, interaction.user.name)
        msg = await voting_channel.send(content=role_mentions if role_mentions else "", embed=e, view=view)

        vote_id = await create_vote(
            interaction.guild.id,
            voting_channel.id,
            msg.id,
            interaction.user.id,
            interaction.user.name,
            target,
            action_type,
            command_type
        )

        view.vote_id = vote_id
        view.message = msg

        await interaction.response.send_message("✅ Vote request submitted!", ephemeral=True)

        emb = discord.Embed(
            title=f"Vote: {action_type}",
            description=f"Target: {target}\nRequested by: {interaction.user.mention}",
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await send_chronology(self.bot, emb)

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(Voting(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(Voting(bot))
