import discord
from typing import Optional
import datetime
import random
import string
from bot.config import EMBED_COLOR_MAIN


def generate_id(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def build_embed(data: dict) -> discord.Embed:
    finished = data.get('finished', False)
    title = data['название']

    if finished:
        embed = discord.Embed(title=title, color=discord.Color.red())
        embed.set_author(name="🔴FINISHED🔴")
    else:
        embed = discord.Embed(title=title, color=EMBED_COLOR_MAIN)

    info = f"**Created by:** {data['author_mention']}\n"
    info += f"**Date:** {data['дата_text']}\n"
    if data.get('комментарий'):
        info += f"**Comment:** {data['комментарий']}\n"
    info += f"**Roles:** {data.get('роли') or 'No restrictions'}"
    embed.description = info

    if data.get('mvp_mention'):
        embed.description += f"\n\n⭐ **MVP:** {data['mvp_mention']}"

    slots = data['слоты']
    members = data.get('members', [])
    marked = data.get('marked', [])
    mvp_id = data.get('mvp_id')

    member_lines = []
    for m in members:
        uid = m['id']
        icons = ""
        if uid == data['author_id']:
            icons += "👑"
        if uid == mvp_id:
            icons += "⭐"
        check = " ✅" if uid in marked else ""
        member_lines.append(f"{icons} <@{uid}>{check}")

    members_text = "\n".join(member_lines) if member_lines else "\u200b"
    embed.add_field(
        name=f"Members ({len(members)}/{slots})",
        value=members_text,
        inline=False
    )

    доп_max = data.get('доп_слоты')
    if доп_max:
        доп_members = data.get('доп_members', [])
        доп_lines = [f"<@{m['id']}>" for m in доп_members]
        доп_text = "\n".join(доп_lines) if доп_lines else "\u200b"
        embed.add_field(
            name=f"Reserve slots ({len(доп_members)}/{доп_max})",
            value=доп_text,
            inline=False
        )

    if data.get('image_url'):
        embed.set_image(url=data['image_url'])

    return embed


class RemindModal(discord.ui.Modal, title="Reminder"):
    text = discord.ui.TextInput(
        label="Reminder text",
        placeholder="Enter text...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    def __init__(self, data: dict, thread: Optional[discord.Thread]):
        super().__init__()
        self.data = data
        self.thread = thread

    async def on_submit(self, interaction: discord.Interaction):
        members = self.data.get('members', [])
        доп_members = self.data.get('доп_members', [])
        all_members = members + доп_members
        mentions = " ".join([f"<@{m['id']}>" for m in all_members])
        remind_text = f"📢 **Reminder about squad «{self.data['название']}»**\n{self.text.value}\n{mentions}"

        target = self.thread if self.thread else interaction.channel
        await target.send(remind_text)

        success_embed = discord.Embed(color=discord.Color.green())
        success_embed.title = "Success"
        success_embed.description = "Notification sent successfully."
        if self.thread:
            success_embed.description += f"\n[Go to message]({self.thread.jump_url})"
        await interaction.response.send_message(embed=success_embed, ephemeral=True)


class ManageView(discord.ui.View):
    def __init__(self, data: dict, original_message: discord.Message, thread: Optional[discord.Thread] = None):
        super().__init__(timeout=300)
        self.data = data
        self.original_message = original_message
        self.thread = thread

    async def update_original(self, interaction: discord.Interaction):
        embed = build_embed(self.data)
        view = PluseView(self.data, self.thread)
        await self.original_message.edit(embed=embed, view=view)

    @discord.ui.button(label="Kick member", style=discord.ButtonStyle.danger, row=0)
    async def kick_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.data.get('members', [])
        kickable = [m for m in members if m['id'] != self.data['author_id']]
        if not kickable:
            await interaction.response.send_message("No members to kick.", ephemeral=True)
            return
        options = [discord.SelectOption(label=m['name'][:100], value=str(m['id'])) for m in kickable]
        select = discord.ui.Select(placeholder="Select a member", options=options)

        async def kick_cb(inter: discord.Interaction):
            uid = int(select.values[0])
            self.data['members'] = [m for m in self.data['members'] if m['id'] != uid]
            if uid in self.data.get('marked', []):
                self.data['marked'].remove(uid)
            await self.update_original(inter)
            await inter.response.send_message(f"✅ <@{uid}> kicked.", ephemeral=True)

        select.callback = kick_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select a member:", view=v, ephemeral=True)

    @discord.ui.button(label="Move", style=discord.ButtonStyle.secondary, row=0)
    async def move_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.data.get('members', [])
        доп = self.data.get('доп_members', [])
        all_m = members + доп
        if not all_m:
            await interaction.response.send_message("No members.", ephemeral=True)
            return
        options = [discord.SelectOption(
            label=m['name'][:100],
            value=str(m['id']),
            description="Main" if any(x['id'] == m['id'] for x in members) else "Reserve slot"
        ) for m in all_m]
        select = discord.ui.Select(placeholder="Select a member to move", options=options)

        async def move_cb(inter: discord.Interaction):
            uid = int(select.values[0])
            in_main = any(m['id'] == uid for m in self.data['members'])
            member_obj = next((m for m in all_m if m['id'] == uid), None)
            if in_main:
                self.data['members'] = [m for m in self.data['members'] if m['id'] != uid]
                self.data.setdefault('доп_members', []).append(member_obj)
                msg = f"✅ <@{uid}> moved to reserve slots."
            else:
                self.data['доп_members'] = [m for m in self.data.get('доп_members', []) if m['id'] != uid]
                self.data['members'].append(member_obj)
                msg = f"✅ <@{uid}> moved to main."
            await self.update_original(inter)
            await inter.response.send_message(msg, ephemeral=True)

        select.callback = move_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select a member:", view=v, ephemeral=True)

    @discord.ui.button(label="Replace", style=discord.ButtonStyle.secondary, row=0)
    async def replace_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.data.get('members', [])
        if not members:
            await interaction.response.send_message("No members.", ephemeral=True)
            return
        options = [discord.SelectOption(label=m['name'][:100], value=str(m['id'])) for m in members]
        select = discord.ui.Select(placeholder="Who to replace?", options=options)

        async def replace_cb(inter: discord.Interaction):
            await inter.response.send_message(
                f"Mention the new member to replace <@{select.values[0]}>",
                ephemeral=True
            )

        select.callback = replace_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select a member to replace:", view=v, ephemeral=True)

    @discord.ui.button(label="Close with mention", style=discord.ButtonStyle.danger, row=0)
    async def close_with_tag(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data['finished'] = True
        members = self.data.get('members', [])
        доп = self.data.get('доп_members', [])
        mentions = " ".join([f"<@{m['id']}>" for m in members + доп])

        embed = build_embed(self.data)
        view = PluseView(self.data, self.thread, finished=True)
        await self.original_message.edit(embed=embed, view=view)

        target = self.thread if self.thread else interaction.channel
        await target.send(f"🔴 **Recruiting finished! Date:** {self.data['дата_text']}\n{mentions}")
        await interaction.response.send_message("✅ Event closed with mention.", ephemeral=True)

    @discord.ui.button(label="Close silently", style=discord.ButtonStyle.danger, row=0)
    async def close_silent(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data['finished'] = True
        members = self.data.get('members', [])
        доп = self.data.get('доп_members', [])

        raid_id = generate_id()
        now = datetime.datetime.now()

        embed = build_embed(self.data)
        view = PluseView(self.data, self.thread, finished=True)
        await self.original_message.edit(embed=embed, view=view)

        log_embed = discord.Embed(title="Event closed", color=discord.Color.orange())
        log_embed.description = f"Event \"{self.data['название']}\" was closed silently"
        log_embed.add_field(name="Event ID", value=raid_id, inline=True)
        log_embed.add_field(name="Title", value=self.data['название'], inline=True)
        log_embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Creator", value=f"<@{self.data['author_id']}>", inline=True)
        log_embed.add_field(name="Members count", value=str(len(members)), inline=True)
        log_embed.add_field(name="Closed at", value=discord.utils.format_dt(now, 'F'), inline=True)

        if members:
            participants = "\n".join([f"<@{m['id']}> (Main)" for m in members])
            if доп:
                participants += "\n" + "\n".join([f"<@{m['id']}> (Reserve)" for m in доп])
            log_embed.add_field(name="Participants list", value=participants, inline=False)

        log_embed.set_footer(text=f"Closed by {interaction.user.name}")
        await interaction.response.send_message(embed=log_embed, ephemeral=True)

    @discord.ui.button(label="Select voice", style=discord.ButtonStyle.secondary, row=1)
    async def choose_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        voice_channels = guild.voice_channels[:25]
        if not voice_channels:
            await interaction.response.send_message("No voice channels.", ephemeral=True)
            return
        options = [discord.SelectOption(label=c.name[:100], value=str(c.id)) for c in voice_channels]
        select = discord.ui.Select(placeholder="Select voice channel", options=options)

        async def vc_cb(inter: discord.Interaction):
            await inter.response.send_message(f"✅ Voice selected: <#{select.values[0]}>", ephemeral=True)

        select.callback = vc_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select voice channel:", view=v, ephemeral=True)

    @discord.ui.button(label="Who's in voice", style=discord.ButtonStyle.secondary, row=1)
    async def who_in_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        lines = []
        for vc in guild.voice_channels:
            for member in vc.members:
                lines.append(f"{member.mention} — {vc.name}")
        if not lines:
            await interaction.response.send_message("Nobody is in voice channels.", ephemeral=True)
        else:
            await interaction.response.send_message("**In voice channels:**\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="Remind", style=discord.ButtonStyle.secondary, row=1)
    async def remind(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemindModal(self.data, self.thread))

    @discord.ui.button(label="Add moderator", style=discord.ButtonStyle.secondary, row=2)
    async def add_mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.data.get('members', [])
        if not members:
            await interaction.response.send_message("No members.", ephemeral=True)
            return
        options = [discord.SelectOption(label=m['name'][:100], value=str(m['id'])) for m in members]
        select = discord.ui.Select(placeholder="Select moderator", options=options)

        async def mod_cb(inter: discord.Interaction):
            uid = int(select.values[0])
            mods = self.data.setdefault('moderators', [])
            if uid not in mods:
                mods.append(uid)
            await inter.response.send_message(f"✅ <@{uid}> set as moderator.", ephemeral=True)

        select.callback = mod_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select moderator:", view=v, ephemeral=True)

    @discord.ui.button(label="Remove moderator", style=discord.ButtonStyle.secondary, row=2)
    async def remove_mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        mods = self.data.get('moderators', [])
        if not mods:
            await interaction.response.send_message("No moderators.", ephemeral=True)
            return
        options = [discord.SelectOption(label=f"<@{uid}>", value=str(uid)) for uid in mods]
        select = discord.ui.Select(placeholder="Select moderator to remove", options=options)

        async def unmod_cb(inter: discord.Interaction):
            uid = int(select.values[0])
            self.data['moderators'] = [m for m in mods if m != uid]
            await inter.response.send_message(f"✅ <@{uid}> removed from moderators.", ephemeral=True)

        select.callback = unmod_cb
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Select moderator:", view=v, ephemeral=True)

    @discord.ui.button(label="Set MVP", style=discord.ButtonStyle.secondary, row=2)
    async def set_mvp(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.data.get('members', [])
        if not members:
            await interaction.response.send_message("No members.", ephemeral=True)
            return
        options = [discord.SelectOption(label=m['name'][:100], value=str(m['id'])) for m in members]
        select = discord.ui.Select(placeholder="Select MVP", options=options)

        async def mvp_cb(inter: discord.Interaction):
            uid = int(select.values[0])
            self.data['mvp_id'] = uid
            self.data['mvp_mention'] = f"<@{uid}>"
            await self.update_original(inter)

            mvp_embed = discord.Embed(color=discord.Color.gold())
            mvp_embed.description = f"⭐ **SQUAD MVP** ⭐\n<@{uid}> was chosen as the most valuable participant!"
            target = self.thread if self.thread else inter.channel
            await target.send(embed=mvp_embed)

            confirm_embed = discord.Embed(title="MVP Selected", color=EMBED_COLOR_MAIN)
            confirm_embed.description = f"Select the participant who will be MVP."
            await inter.response.send_message(embed=confirm_embed, ephemeral=True)

        select.callback = mvp_cb

        mvp_embed = discord.Embed(title="Select MVP", color=EMBED_COLOR_MAIN)
        mvp_embed.description = "Select the participant who will be MVP."
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message(embed=mvp_embed, view=v, ephemeral=True)

    @discord.ui.button(label="Edit Event", style=discord.ButtonStyle.secondary, row=2)
    async def edit_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Event editing feature is under development.", ephemeral=True)

    @discord.ui.button(label="Respawn", style=discord.ButtonStyle.primary, row=3)
    async def respawn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data['finished'] = False
        embed = build_embed(self.data)
        view = PluseView(self.data, self.thread)
        await self.original_message.edit(embed=embed, view=view)
        await interaction.response.send_message("✅ Event respawned.", ephemeral=True)


class PluseView(discord.ui.View):
    def __init__(self, data: dict, thread: Optional[discord.Thread] = None, finished: bool = False):
        super().__init__(timeout=None)
        self.data = data
        self.thread = thread
        self.finished = finished or data.get('finished', False)

    def is_mod(self, user_id: int) -> bool:
        return (user_id == self.data['author_id'] or
                user_id in self.data.get('moderators', []))

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="pluse:join", row=0)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            await interaction.response.send_message("Event is finished.", ephemeral=True)
            return

        uid = interaction.user.id
        members = self.data.setdefault('members', [])
        доп = self.data.setdefault('доп_members', [])

        if any(m['id'] == uid for m in members + доп):
            await interaction.response.send_message("You are already in the squad!", ephemeral=True)
            return

        if len(members) >= self.data['слоты']:
            await interaction.response.send_message("No free slots!", ephemeral=True)
            return

        members.append({'id': uid, 'name': interaction.user.display_name})
        embed = build_embed(self.data)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Join reserve slot", style=discord.ButtonStyle.blurple, custom_id="pluse:join_extra", row=0)
    async def join_extra(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            await interaction.response.send_message("Event is finished.", ephemeral=True)
            return

        доп_max = self.data.get('доп_слоты')
        if not доп_max:
            await interaction.response.send_message("Reserve slots not available.", ephemeral=True)
            return

        uid = interaction.user.id
        members = self.data.get('members', [])
        доп = self.data.setdefault('доп_members', [])

        if any(m['id'] == uid for m in members + доп):
            await interaction.response.send_message("You are already in the squad!", ephemeral=True)
            return

        if len(доп) >= доп_max:
            await interaction.response.send_message("No free reserve slots!", ephemeral=True)
            return

        доп.append({'id': uid, 'name': interaction.user.display_name})
        embed = build_embed(self.data)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.danger, custom_id="pluse:leave", row=0)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        members = self.data.get('members', [])
        доп = self.data.get('доп_members', [])

        in_main = any(m['id'] == uid for m in members)
        in_extra = any(m['id'] == uid for m in доп)

        if not in_main and not in_extra:
            await interaction.response.send_message("You are not in the squad.", ephemeral=True)
            return

        if in_main:
            self.data['members'] = [m for m in members if m['id'] != uid]
            if uid in self.data.get('marked', []):
                self.data['marked'].remove(uid)
        else:
            self.data['доп_members'] = [m for m in доп if m['id'] != uid]

        embed = build_embed(self.data)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Check in", style=discord.ButtonStyle.success, custom_id="pluse:mark", row=0)
    async def mark(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        members = self.data.get('members', [])

        if not any(m['id'] == uid for m in members):
            await interaction.response.send_message("You are not in the main roster.", ephemeral=True)
            return

        marked = self.data.setdefault('marked', [])
        if uid in marked:
            marked.remove(uid)
            await interaction.response.send_message("✅ Check-in removed.", ephemeral=True)
        else:
            marked.append(uid)
            await interaction.response.send_message("✅ Checked in!", ephemeral=True)

        embed = build_embed(self.data)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Manage", style=discord.ButtonStyle.secondary, custom_id="pluse:manage", row=1)
    async def manage(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_mod(interaction.user.id):
            await interaction.response.send_message(
                "❌ Only the author or a moderator can manage the event.", ephemeral=True
            )
            return

        manage_embed = discord.Embed(
            description="Select an action to manage the event:",
            color=discord.Color.red()
        )
        view = ManageView(self.data, interaction.message, self.thread)
        await interaction.response.send_message(embed=manage_embed, view=view, ephemeral=True)
