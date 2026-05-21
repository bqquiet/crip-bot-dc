import discord
from discord import app_commands
from discord.ext import commands
from bot.config import GUILD_OBJ, APPLICATION_RESULT_CHANNEL_ID
from bot.ui.applications import ApplicationPanelView

LINE = "-# ~~ᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠᅠ~~"

BANNER_PATH = "banner.png"

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="send_application_panel", description="Send the family application panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_application_panel(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        text_embed = discord.Embed(
            title="<a:1513blackspinningpixelheart:1484967290830196880>  We're accepting applications to join CRIPSIZE  <a:1513blackspinningpixelheart:1484967290830196880>",
            description=(
                "**TO JOIN THE FAMILY** you need rollbacks from MP **and** GUNGAME.\n\n"

                "**Application review time: 3 to 5 business days.** The decision is sent by the bot to "
                "your DMs + a thread is opened where you will most likely be asked to provide screenshots "
                "of your characters and will be called for a **voice interview**. No response within the given time means rejection.\n\n"

                "> <:vnimanie:1484967341258178742>  Family applications are accepted only on server **Boston. (12)**\n"
                "> **ALL APPLICATIONS MINIMUM AGE 15!**\n\n"

                "-# Please read the application template carefully — it also contains important information.\n"
                "-# The CRIPSIZE role application requires full rollbacks from GG and MP (MCL, VZZ, CAPTS).\n\n"

                "**Additional rules in the application:**\n"
                "-# • GG rollbacks must have been recorded no more than **1 week** ago.\n"
                "-# • MP rollbacks must have been recorded no more than **60 days** ago.\n"
                "-# • Minimum GG rollback length — **at least 5 minutes.**\n"
                "-# • Any violation of rollback submission conditions will likely result in **rejection** without exceptions.\n\n"

                "> <:vnimanie:1484967341258178742>  After submitting your application **watch the channel <#1480524874584821800>** in the official CRIPSIZE Discord server. "
                "The recruiter will call you **only in the CRIPSIZE Discord** — not in DMs, not in another server.\n\n"

                "-# If you ignore the recruiter in DMs after your application is accepted — the application will be **automatically rejected**, "
                "and you will need to resubmit.\n"
                "-# If you were rejected — a **7-day cooldown** applies before reapplying.\n\n"

                "> **TAKE THE APPLICATION TEMPLATE SERIOUSLY.** Read and check all fields carefully. "
                "Messages in DMs like 'Didn't see it', 'Misread', 'Didn't understand', 'Made a mistake', etc. "
                "will be treated as rejection.\n\n"

                f"{LINE}\n"
                "• Please read the conditions above carefully and then choose the application type.\n"
                f"{LINE}\n\n"

                "**• Choose an application type**"
            ),
            color=discord.Color.dark_theme()
        )

        try:
            image_file = discord.File(BANNER_PATH, filename="banner.png")
        except FileNotFoundError:
            await interaction.followup.send(f"Error: Image file not found at `{BANNER_PATH}`!", ephemeral=True)
            return

        await interaction.channel.send(file=image_file, embed=text_embed, view=ApplicationPanelView())

        await interaction.followup.send("Panel sent successfully!", ephemeral=True)

async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(Applications(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(Applications(bot))
