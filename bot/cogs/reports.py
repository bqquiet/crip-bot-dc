import discord
from discord import app_commands
from discord.ext import commands
import datetime
from bot.config import GUILD_OBJ, EMBED_COLOR_MAIN
from bot.ui import WarpunView, AfkReportView, FarmAfkView, PromoteView, ContractView
from bot.database import get_active_afk_reports

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn-template", description="Send the warn removal template")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn_template_slash(self, interaction: discord.Interaction):
        e = discord.Embed(title="⚖️ Warn Removal Template", description=(
            "To remove an active warning, you must deposit **$50,000** into the family account and fill in the form below:\n\n"
            "1. **Your nickname:** (First_Last)\n"
            "2. **Your static ID:** (#0000)\n"
            "3. **Reason for warn:** (What the warning was issued for)\n"
            "4. **Proof:** (Screenshot of the family balance deposit)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "💡 **Example:**\n"
            "1. Queran Cripsize\n"
            "2. #201574\n"
            "3. Missed MP without notice\n"
            "4. [Screenshot of $50,000 deposit]\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "⚠️ **Important:**\n"
            "• Cost to remove one warn — **$50,000**.\n"
            "• Screenshot must be complete (showing date, time, and transfer amount).\n"
            "• Warn is considered removed only after approval by senior staff."
        ), color=discord.Color.red())
        await interaction.response.send_message("✅ Template sent.", ephemeral=True)
        await interaction.channel.send(embed=e, view=WarpunView())

    @app_commands.command(name="afkreport", description="Send the AFK report template")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def afkreport_slash(self, interaction: discord.Interaction):
        e = discord.Embed(title="💤 AFK Report Template", description=(
            "If you plan to temporarily step away from family activities or take a break, fill in the form below so there are no questions about your activity:\n\n"
            "1. **Your nickname:** (First_Last)\n"
            "2. **AFK reason:** (Rest / Study / Work / Personal circumstances)\n"
            "3. **Absence time:** (Specify hours, e.g.: 14:00 to 22:00)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "💡 **Example:**\n"
            "1. Queran Cripsize\n"
            "2. Study (exam preparation)\n"
            "3. 12:00 — 21:00 (9 hours)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "⚠️ **Rules:**\n"
            "• Report must be submitted before going AFK."
        ), color=discord.Color.blue())
        await interaction.response.send_message("✅ Template sent.", ephemeral=True)
        await interaction.channel.send(embed=e, view=AfkReportView())

    @app_commands.command(name="farmafk", description="Send the Farm AFK report template")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def farmafk_slash(self, interaction: discord.Interaction):
        e = discord.Embed(title="📑 Report Template", description=(
            "To have your report accepted, send a message strictly in the following format:\n\n"
            "1. **Your nickname:** (First_Last)\n"
            "2. **Chosen option:** (Money / 10 MP / 20 Contracts)\n"
            "3. **Leave period:** (from DD.MM to DD.MM)\n"
            "4. **Proof:** (Attach screenshot to the message)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "💡 **Example:**\n"
            "1. Queran Cripsize\n"
            "2. Money ($350,000)\n"
            "3. 01.02 - 08.02\n"
            "4. [Transfer screenshot]\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "⚠️ **Important:**\n"
            "• Report must be submitted before going AFK.\n"
            "• Proof must be attached to the message.\n"
            "• Report is accepted only after approval by senior staff."
        ), color=discord.Color.purple())
        await interaction.response.send_message("✅ Template sent.", ephemeral=True)
        await interaction.channel.send(embed=e, view=FarmAfkView())

    @app_commands.command(name="promote", description="Send the promotion application template")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def promote_slash(self, interaction: discord.Interaction):
        e = discord.Embed(title="📈 Promotion Application Template", description=(
            "To have your promotion application reviewed, fill in the form below:\n\n"
            "1. **Your nickname:** (First_Last)\n"
            "2. **Current rank ➔ Rank you're applying for:** (e.g.: [2] ➔ [4])\n"
            "3. **Work completed:** (Brief description: 25 Drug Courier / Last Name / GG Rollback)\n"
            "4. **Proof:** (Link to rollback or screenshots)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "💡 **Example:**\n"
            "1. Queran Cripsize\n"
            "2. [2] Trainee ➔ [4] Verified\n"
            "3. Changed last name, uploaded GG rollback, completed 25 drug courier contracts.\n"
            "4. [Link to video/screenshots]\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "⚠️ **Notes:**\n"
            "• Changing last name to Cripsize is mandatory for the first promotion.\n"
            "• GG shooting rollbacks must be of good quality.\n"
            "• Tablet screenshots (damage) must be clear and complete."
        ), color=discord.Color.gold())
        await interaction.response.send_message("✅ Template sent.", ephemeral=True)
        await interaction.channel.send(embed=e, view=PromoteView())

    @app_commands.command(name="contract", description="Send the contract resource request template")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def contract_slash(self, interaction: discord.Interaction):
        e = discord.Embed(title="🌿 Contract Report Template", description=(
            "If you need resources to complete contracts, fill in the form below:\n\n"
            "1. **Your nickname:** (First_Last)\n"
            "2. **Your static ID:** (#0000)\n"
            "3. **What exactly?:** (Green, Blue, White)\n"
            "4. **Required quantity:** (e.g.: 20 pieces)\n"
            "5. **Your courier rank:** (e.g.: 3)\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "💡 **Example:**\n"
            "1. Queran Cripsize\n"
            "2. #201574\n"
            "3. Blue\n"
            "4. 200\n"
            "5. Rank 5\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
            "⚠️ **Rules:**\n"
            "• Resources are issued strictly for completing family contracts.\n"
            "• Selling or leaking resources — immediate family exclusion (BlackList)."
        ), color=discord.Color.green())
        await interaction.response.send_message("✅ Template sent.", ephemeral=True)
        await interaction.channel.send(embed=e, view=ContractView())

    @app_commands.command(name="afk_list", description="List of users in AFK today")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def afk_list(self, interaction: discord.Interaction):
        reports = await get_active_afk_reports()

        afk_list = []
        farmaf_list = []

        for user_id, user_name, data, report_type in reports:
            mention = f"<@{user_id}>"
            if report_type == 'afk':
                time = data.get('time', '—')
                afk_list.append(f"{mention} | {time}")
            elif report_type == 'farmafk':
                period = data.get('period', '—')
                farmaf_list.append(f"{mention} | {period}")

        embed = discord.Embed(
            title="AFK Users List",
            color=EMBED_COLOR_MAIN
        )

        if not afk_list and not farmaf_list:
            embed.description = "No users are AFK today"
        else:
            afk_text = "\n".join(afk_list) if afk_list else "No users"
            embed.add_field(name="👤 Regular AFK", value=afk_text, inline=False)

            farmaf_text = "\n".join(farmaf_list) if farmaf_list else "No users"
            embed.add_field(name="🌱 Farm AFK", value=farmaf_text, inline=False)

        embed.set_footer(text=f"Updated: {datetime.datetime.now().strftime('%H:%M')}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(Reports(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(Reports(bot))
