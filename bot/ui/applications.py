import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from datetime import datetime, timedelta

# === CHANNELS ===
REVIEW_CHANNEL_ID = 1480539070143664218
RESULT_CHANNEL_ID = 1480524874584821800
WAITING_ROOM_CHANNEL_ID = 1450523333446860892

RESULT_IMAGE_PATH = "avatar.png"
COOLDOWN_FILE = "cooldowns.json"

# --- COOLDOWN LOGIC ---
def load_cooldowns():
    if os.path.exists(COOLDOWN_FILE):
        try:
            with open(COOLDOWN_FILE, "r") as f:
                data = json.load(f)
                return {int(k): datetime.fromisoformat(v) for k, v in data.items()}
        except: return {}
    return {}

def save_cooldowns(cooldowns):
    with open(COOLDOWN_FILE, "w") as f:
        data = {str(k): v.isoformat() for k, v in cooldowns.items()}
        json.dump(data, f)

application_cooldowns = load_cooldowns()

# --- HELPER FUNCTION FOR STATUS UPDATES ---
async def send_status_update(interaction: discord.Interaction, applicant_id: int, status: str, reason: str = None):
    result_channel = interaction.guild.get_channel(RESULT_CHANNEL_ID)
    if not result_channel: return
    applicant = interaction.guild.get_member(applicant_id)
    reviewer = interaction.user
    app_mention = applicant.mention if applicant else f"<@{applicant_id}>"
    embed = discord.Embed(timestamp=discord.utils.utcnow())
    if status == "review":
        embed.color = discord.Color.orange()
        embed.description = "> ### Your application is under review!"
    elif status == "accepted":
        embed.color = discord.Color.green()
        embed.description = "> ### Application result"
    elif status == "rejected":
        embed.color = discord.Color.red()
        embed.description = "> ### Application result"
    embed.add_field(name="Applicant", value=f"{app_mention}\n`ID: {applicant_id}`", inline=True)
    embed.add_field(name="Reviewed by", value=f"{reviewer.mention}\n`ID: {reviewer.id}`", inline=True)
    if status == "accepted":
        embed.add_field(name="Status", value="Accepted <:Yes1:1481213779999068273>", inline=True)
        embed.description += f"\n\nFor the voice interview please wait in:\n<#{WAITING_ROOM_CHANNEL_ID}>"
    elif status == "rejected":
        embed.add_field(name="Status", value="Rejected <:No1:1481213722608275507>", inline=True)
        if reason: embed.add_field(name="Reason", value=reason, inline=False)
    try:
        if os.path.exists(RESULT_IMAGE_PATH):
            file = discord.File(RESULT_IMAGE_PATH, filename="status_img.png")
            embed.set_thumbnail(url="attachment://status_img.png")
            await result_channel.send(content=app_mention if status != "review" else None, embed=embed, file=file)
            return
    except: pass
    await result_channel.send(content=app_mention if status != "review" else None, embed=embed)

def get_applicant_id(embed: discord.Embed) -> int:
    try:
        footer_text = embed.footer.text
        return int(footer_text.split(":")[1].split("•")[0].strip())
    except: return 0

# --- MODALS ---
class ApplicationModal(discord.ui.Modal, title="CRIPSIZE FamQ Application Form"):
    name_age = discord.ui.TextInput(
        label="Name | Your Age",
        placeholder="Example: Andrew | 18 years old",
        required=True
    )
    nickname_server = discord.ui.TextInput(
        label="Your in-game Nickname",
        placeholder="Example: Queran Cripsize",
        required=True
    )
    playtime = discord.ui.TextInput(
        label="Prime time",
        placeholder="Example: 6 hours on average | 17:00-23:00",
        required=True
    )
    experience = discord.ui.TextInput(
        label="Gaming experience",
        placeholder="Describe where you played and why you left your previous family. Why do you want to join us?",
        style=discord.TextStyle.paragraph,
        required=True
    )
    video_proof = discord.ui.TextInput(
        label="Rollback (GG + MP)",
        placeholder="Fresh rollback from MP and GUNGAME. Video link.",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        application_cooldowns[interaction.user.id] = datetime.now()
        save_cooldowns(application_cooldowns)

        user_embed = discord.Embed(
            title="<:Yes1:1481213779999068273> Application submitted successfully!",
            description="Your application has been sent to the recruiters. Wait for a response in <#1480524874584821800>.",
            color=discord.Color.dark_theme()
        )
        await interaction.response.send_message(embed=user_embed, ephemeral=True)

        review_channel = interaction.guild.get_channel(REVIEW_CHANNEL_ID)
        if not review_channel: return

        line = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

        embed = discord.Embed(
            title="<:message:1481209442145009717> New membership application",
            description=f"Submitted by: {interaction.user.mention}\n`ID: {interaction.user.id}`\n\n**APPLICANT FORM:**\n{line}",
            color=discord.Color.dark_theme(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="<:role_update:1481213741818445945> Name | Age", value=f"```\n{self.name_age.value}\n```", inline=False)
        embed.add_field(name="<:web1:1481213776119464037> In-game Nickname", value=f"```\n{self.nickname_server.value}\n```", inline=False)
        embed.add_field(name="<:logs:1481209424931721377> Prime time", value=f"```\n{self.playtime.value}\n```", inline=False)
        embed.add_field(name="<:info:1481209397811089468> Gaming experience", value=f"```\n{self.experience.value}\n```", inline=False)
        embed.add_field(name="<:announcement:1481209285932355626> Rollback (GG + MP)", value=f"```\n{self.video_proof.value}\n```", inline=False)

        if interaction.user.display_avatar:
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.set_footer(text=f"Applicant ID for buttons: {interaction.user.id} •")
        await review_channel.send(embed=embed, view=ApplicationNewView())

# --- VIEWS ---
class ApplicationRejectModal(discord.ui.Modal, title="Reject Application"):
    reason = discord.ui.TextInput(label="Rejection reason", style=discord.TextStyle.paragraph, required=True)
    def __init__(self, target_user_id: int, original_message: discord.Message):
        super().__init__(); self.target_user_id = target_user_id; self.original_message = original_message
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Application rejected.", ephemeral=True)
        embed = self.original_message.embeds[0]
        embed.color = discord.Color.red(); embed.title = "Application Rejected"
        embed.clear_fields(); embed.add_field(name="Reviewed by", value=interaction.user.mention, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        await self.original_message.edit(embed=embed, view=None)
        await send_status_update(interaction, self.target_user_id, "rejected", self.reason.value)

class ApplicationReviewView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="app_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = get_applicant_id(interaction.message.embeds[0])
        await interaction.response.send_message("Application accepted.", ephemeral=True)
        embed = interaction.message.embeds[0]; embed.color = discord.Color.green(); embed.title = "Application Accepted"
        embed.clear_fields(); embed.add_field(name="Reviewed by", value=interaction.user.mention, inline=False)
        await interaction.message.edit(embed=embed, view=None)
        if user_id: await send_status_update(interaction, user_id, "accepted")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red, custom_id="app_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = get_applicant_id(interaction.message.embeds[0])
        await interaction.response.send_modal(ApplicationRejectModal(user_id, interaction.message))

class ApplicationNewView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Review", style=discord.ButtonStyle.blurple, custom_id="app_review")
    async def review_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = get_applicant_id(interaction.message.embeds[0])
        embed = interaction.message.embeds[0]; embed.color = discord.Color.orange(); embed.title = "Application Under Review"
        embed.add_field(name="Taken for review by", value=interaction.user.mention, inline=False)
        await interaction.response.edit_message(embed=embed, view=ApplicationReviewView())
        if user_id: await send_status_update(interaction, user_id, "review")

class ApplicationSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Apply to CRIPSIZE FamQ", emoji="<:boston:1481209293133840424>")]
        super().__init__(placeholder="Your choice", min_values=1, max_values=1, options=options, custom_id="app_select")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        await interaction.message.edit(view=ApplicationPanelView())

        if user_id in application_cooldowns:
            delta = datetime.now() - application_cooldowns[user_id]
            if delta < timedelta(days=7):
                rem = timedelta(days=7) - delta
                cd_embed = discord.Embed(
                    title="<:No1:1481213722608275507> Access restricted",
                    description=f"You have already submitted an application to our family.\n\nYou can reapply in:\n**{rem.days}d {rem.seconds//3600}h {(rem.seconds//60)%60}m**",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=cd_embed, ephemeral=True)

        await interaction.response.send_modal(ApplicationModal())

class ApplicationPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.add_item(ApplicationSelect())

class ApplicationsCog(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @app_commands.command(name="send_application_panel", description="Send the application panel")
    @app_commands.default_permissions(administrator=True)
    async def send_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Join CRIPSIZE FamQ!", description="Choose an option below to fill out an application.", color=discord.Color.dark_theme())
        await interaction.response.send_message(embed=embed, view=ApplicationPanelView())

async def setup(bot):
    await bot.add_cog(ApplicationsCog(bot))
