import discord
from typing import Optional, Tuple
from bot.config import TEMPVOICE_CREATE_CHANNEL_ID, EMBED_COLOR_MAIN
from bot.database import tv_get_owner, tv_set, tv_delete
from bot.utils import is_tempvoice_channel, _gold_warn_embed, _parse_member

class _BaseTempVoiceModal(discord.ui.Modal):
    def __init__(self, panel: "TempVoicePanel", title: str):
        super().__init__(title=title)
        self.panel = panel

    async def _ctx(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        ok, vc = await self.panel.ensure_tempvoice(interaction)
        return vc if ok else None

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        try:
            await interaction.response.send_message('❌ An error occurred. Please try again.', ephemeral=True)
        except Exception:
            try:
                await interaction.followup.send('❌ An error occurred. Please try again.', ephemeral=True)
            except Exception:
                pass

class RenameVoiceModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.name = discord.ui.TextInput(
            label="Channel name",
            placeholder="Empty = reset to your name",
            required=False,
            max_length=32
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        new_name = (self.name.value or "").strip()
        if new_name:
            await vc.edit(name=new_name)
        else:
            await vc.edit(name=f"{interaction.user.display_name}")
        await interaction.response.send_message("✅ Done.", ephemeral=True)

class LimitVoiceModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.limit = discord.ui.TextInput(
            label="User limit (0-99)",
            placeholder="0 = no limit",
            required=True,
            max_length=2
        )
        self.add_item(self.limit)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        try:
            n = int((self.limit.value or "").strip())
        except ValueError:
            return await interaction.response.send_message("❌ Enter a number 0-99.", ephemeral=True)
        if n < 0 or n > 99:
            return await interaction.response.send_message("❌ Limit must be 0-99.", ephemeral=True)
        await vc.edit(user_limit=n)
        await interaction.response.send_message("✅ Done.", ephemeral=True)

class AccessModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.action = discord.ui.TextInput(
            label="Access: lock / unlock",
            placeholder="lock or unlock",
            required=True,
            max_length=10
        )
        self.add_item(self.action)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        act = (self.action.value or "").strip().lower()
        everyone = interaction.guild.default_role
        if act == "lock":
            ow = vc.overwrites_for(everyone)
            ow.connect = False
            await vc.set_permissions(everyone, overwrite=ow)
            await interaction.response.send_message("🔒 Channel locked.", ephemeral=True)
        elif act == "unlock":
            ow = vc.overwrites_for(everyone)
            ow.connect = None
            await vc.set_permissions(everyone, overwrite=ow)
            await interaction.response.send_message("🔓 Channel unlocked.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Enter `lock` or `unlock`.", ephemeral=True)

class ChatModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.action = discord.ui.TextInput(
            label="Chat: on / off",
            placeholder="on or off",
            required=True,
            max_length=3
        )
        self.add_item(self.action)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        act = (self.action.value or "").strip().lower()
        everyone = interaction.guild.default_role
        if act == "off":
            ow = vc.overwrites_for(everyone)
            ow.send_messages = False
            await vc.set_permissions(everyone, overwrite=ow)
            await interaction.response.send_message("💬 Chat disabled.", ephemeral=True)
        elif act == "on":
            ow = vc.overwrites_for(everyone)
            ow.send_messages = None
            await vc.set_permissions(everyone, overwrite=ow)
            await interaction.response.send_message("💬 Chat enabled.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Enter `on` or `off`.", ephemeral=True)

class MemberActionModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel", label: str, need_reason: bool = False):
        super().__init__(panel, title="TEMPVOICE")
        self.member = discord.ui.TextInput(
            label=label,
            placeholder="Paste @mention or ID",
            required=True,
            max_length=64
        )
        self.add_item(self.member)
        self.reason = None
        if need_reason:
            self.reason = discord.ui.TextInput(
                label="Reason (optional)",
                placeholder="...",
                required=False,
                max_length=200
            )
            self.add_item(self.reason)

    async def _get_member(self, interaction: discord.Interaction) -> Optional[discord.Member]:
        return await _parse_member(interaction.guild, self.member.value)

class TrustModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Trust user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        ow = vc.overwrites_for(target)
        ow.view_channel = True
        ow.connect = True
        await vc.set_permissions(target, overwrite=ow)
        await interaction.response.send_message("✅ Access granted.", ephemeral=True)

class UntrustModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Remove trust from user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        await vc.set_permissions(target, overwrite=None)
        await interaction.response.send_message("✅ Access reset.", ephemeral=True)

class InviteModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Invite user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        ow = vc.overwrites_for(target)
        ow.view_channel = True
        ow.connect = True
        await vc.set_permissions(target, overwrite=ow)
        await interaction.response.send_message("📩 Access granted.", ephemeral=True)

class KickModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Kick user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        if target.voice and target.voice.channel and target.voice.channel.id == vc.id:
            await target.move_to(None)
        await interaction.response.send_message("👢 Kicked.", ephemeral=True)

class BanModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Ban user", need_reason=True)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        ow = vc.overwrites_for(target)
        ow.view_channel = True
        ow.connect = False
        await vc.set_permissions(target, overwrite=ow)
        if target.voice and target.voice.channel and target.voice.channel.id == vc.id:
            await target.move_to(None)
        await interaction.response.send_message("⛔ Banned from this voice channel.", ephemeral=True)

class UnbanModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Unban user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        ow = vc.overwrites_for(target)
        ow.connect = None
        await vc.set_permissions(target, overwrite=ow)
        await interaction.response.send_message("♻️ Unbanned from this voice channel.", ephemeral=True)

class RegionModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.region = discord.ui.TextInput(
            label="Region (auto/europe/us-east/us-west)",
            placeholder="auto",
            required=True,
            max_length=16
        )
        self.add_item(self.region)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        r = (self.region.value or "").strip().lower()
        if r == "auto":
            await vc.edit(rtc_region=None)
        elif r in ("europe", "eu"):
            await vc.edit(rtc_region="europe")
        elif r in ("us-east", "useast", "east"):
            await vc.edit(rtc_region="us-east")
        elif r in ("us-west", "uswest", "west"):
            await vc.edit(rtc_region="us-west")
        else:
            return await interaction.response.send_message("❌ Unknown region. Try auto/europe/us-east/us-west.", ephemeral=True)
        await interaction.response.send_message("🌍 Region changed.", ephemeral=True)

class TransferModal(MemberActionModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, label="Transfer to user")

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        target = await self._get_member(interaction)
        if not target:
            return await interaction.response.send_message("❌ User not found.", ephemeral=True)
        await tv_set(interaction.guild.id, target.id, vc.id)
        await interaction.response.send_message("🔁 Ownership transferred.", ephemeral=True)

class DeleteConfirmModal(_BaseTempVoiceModal):
    def __init__(self, panel: "TempVoicePanel"):
        super().__init__(panel, title="TEMPVOICE")
        self.confirm = discord.ui.TextInput(
            label='Type "DELETE" to confirm',
            placeholder="DELETE",
            required=True,
            max_length=6
        )
        self.add_item(self.confirm)

    async def on_submit(self, interaction: discord.Interaction):
        vc = await self._ctx(interaction)
        if not vc:
            return
        if (self.confirm.value or "").strip().upper() != "DELETE":
            return await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        await tv_delete(interaction.guild.id, vc.id)
        await vc.delete(reason="TempVoice delete")
        await interaction.response.send_message("🗑️ Channel deleted.", ephemeral=True)

class TempVoicePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item=None) -> None:
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    async def ensure_tempvoice(self, interaction: discord.Interaction) -> Tuple[bool, Optional[discord.VoiceChannel]]:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False, None

        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            create_ch = interaction.guild.get_channel(TEMPVOICE_CREATE_CHANNEL_ID)
            create_mention = create_ch.mention if create_ch else "**the create channel**"
            e = _gold_warn_embed("Notice!", f"You are not currently in a voice channel.\nFirst join {create_mention}.")
            await interaction.response.send_message(embed=e, ephemeral=True)
            return False, None

        if not await is_tempvoice_channel(vc):
            create_ch = interaction.guild.get_channel(TEMPVOICE_CREATE_CHANNEL_ID)
            create_mention = create_ch.mention if create_ch else "**the create channel**"
            e = _gold_warn_embed("Notice!", f"You are not in a **TempVoice** channel.\nFirst join {create_mention}.")
            await interaction.response.send_message(embed=e, ephemeral=True)
            return False, None

        owner_id = await tv_get_owner(interaction.guild.id, vc.id)
        if owner_id and owner_id != interaction.user.id:
            e = _gold_warn_embed("Notice!", "This is not your channel. Only the owner can manage it.")
            await interaction.response.send_message(embed=e, ephemeral=True)
            return False, None

        return True, vc

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🏷️", custom_id="tv:name", row=0)
    async def btn_name(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(RenameVoiceModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="👥", custom_id="tv:limit", row=0)
    async def btn_limit(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(LimitVoiceModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🛡️", custom_id="tv:access", row=0)
    async def btn_access(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(AccessModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🛠️", custom_id="tv:manage", row=0)
    async def btn_manage(self, interaction: discord.Interaction, _: discord.ui.Button):
        ok, _vc = await self.ensure_tempvoice(interaction)
        if not ok:
            return
        e = discord.Embed(
            title="TEMPVOICE",
            description=(
                "**Available actions:**\n"
                "🏷️ Name • 👥 Limit • 🛡️ Access • 💬 Chat\n"
                "➕ Trust • ➖ Untrust • 📩 Invite • 👢 Kick\n"
                "🌍 Region • ⛔ Ban • ♻️ Unban • 👑 Claim • 🔁 Transfer • 🗑️ Delete"
            ),
            color=EMBED_COLOR_MAIN
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="💬", custom_id="tv:chat", row=0)
    async def btn_chat(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(ChatModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="➕", custom_id="tv:trust", row=1)
    async def btn_trust(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(TrustModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="➖", custom_id="tv:untrust", row=1)
    async def btn_untrust(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(UntrustModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="📩", custom_id="tv:invite", row=1)
    async def btn_invite(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(InviteModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="👢", custom_id="tv:kick", row=1)
    async def btn_kick(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(KickModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🌍", custom_id="tv:region", row=1)
    async def btn_region(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(RegionModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⛔", custom_id="tv:ban", row=2)
    async def btn_ban(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(BanModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="♻️", custom_id="tv:unban", row=2)
    async def btn_unban(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(UnbanModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="👑", custom_id="tv:claim", row=2)
    async def btn_claim(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Error.", ephemeral=True)
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if not isinstance(vc, discord.VoiceChannel):
            return await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
        if not await is_tempvoice_channel(vc):
            create_ch = interaction.guild.get_channel(TEMPVOICE_CREATE_CHANNEL_ID)
            create_mention = create_ch.mention if create_ch else "**the create channel**"
            e = _gold_warn_embed("Notice!", f"You are not in a **TempVoice** channel.\nFirst join {create_mention}.")
            return await interaction.response.send_message(embed=e, ephemeral=True)
        owner_id = await tv_get_owner(interaction.guild.id, vc.id)
        if owner_id == interaction.user.id:
            return await interaction.response.send_message("You are already the owner.", ephemeral=True)
        if owner_id:
            owner = interaction.guild.get_member(owner_id)
            if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == vc.id:
                return await interaction.response.send_message("The owner is still in the channel.", ephemeral=True)
        await tv_set(interaction.guild.id, interaction.user.id, vc.id)
        await interaction.response.send_message("👑 You are now the owner.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="tv:transfer", row=2)
    async def btn_transfer(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(TransferModal(self))

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="tv:delete", row=2)
    async def btn_delete(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(DeleteConfirmModal(self))
