import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import datetime
from bot.config import GUILD_OBJ, EMBED_COLOR_MAIN
from bot.database import save_pluse_message


class Pluse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pluse", description="Create a squad event with your settings")
    @app_commands.describe(
        title="Enter the desired event title",
        date="Date and time (format: DD.MM.YYYY HH:MM)",
        slots="Maximum number of participants",
        roles="Tag roles to restrict access (e.g. @role1 @role2 @role3)",
        extra_slots="Maximum number of reserve participants",
        comment="Optional comment for the event",
        thread="Thread name to create (leave empty to skip)",
        image="Attach an image if needed"
    )
    async def pluse_slash(
        self,
        interaction: discord.Interaction,
        title: str,
        date: str,
        slots: int,
        roles: Optional[str] = None,
        extra_slots: Optional[int] = None,
        comment: Optional[str] = None,
        thread: Optional[str] = None,
        image: Optional[discord.Attachment] = None
    ):
        from bot.ui.pluse import PluseView, build_embed

        try:
            event_time = datetime.datetime.strptime(date, "%d.%m.%Y %H:%M")
            event_time_utc = event_time - datetime.timedelta(hours=3)
            event_time_utc = event_time_utc.replace(tzinfo=datetime.timezone.utc)
            date_text = f"{discord.utils.format_dt(event_time_utc, 'F')} ({discord.utils.format_dt(event_time_utc, 'R')})"
        except ValueError:
            date_text = date

        image_url = image.url if image else None

        data = {
            'название': title,
            'дата_text': date_text,
            'слоты': slots,
            'роли': roles,
            'доп_слоты': extra_slots,
            'комментарий': comment,
            'author_id': interaction.user.id,
            'author_mention': interaction.user.mention,
            'members': [],
            'доп_members': [],
            'moderators': [],
            'marked': [],
            'mvp_id': None,
            'mvp_mention': None,
            'image_url': image_url,
            'finished': False,
        }

        embed = build_embed(data)
        view = PluseView(data)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        created_thread = None
        if thread:
            try:
                created_thread = await message.create_thread(name=thread)
            except Exception as e:
                print(f"Error creating thread: {e}")

        if created_thread:
            view_with_thread = PluseView(data, thread=created_thread)
            await message.edit(view=view_with_thread)

        await save_pluse_message(message.id, interaction.channel.id, interaction.user.id, title)

    @app_commands.command(name="mptag", description="Send a message with @everyone three times")
    @app_commands.describe(message="Message to send")
    async def mptag_slash(self, interaction: discord.Interaction, message: str):
        for _ in range(3):
            await interaction.channel.send(f"@everyone {message}")
        await interaction.response.send_message("✅ Sent.", ephemeral=True)


async def setup(bot):
    if GUILD_OBJ:
        await bot.add_cog(Pluse(bot), guilds=[GUILD_OBJ])
    else:
        await bot.add_cog(Pluse(bot))
