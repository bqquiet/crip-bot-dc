import discord
import re
from typing import Optional
from bot.config import REPORT_ROLES
from bot.database import (
    approve_report, reject_report, get_report, update_contract_stats,
    add_contract_request, get_contract_stats, get_contract_history,
    create_report, clear_user_contracts
)

class ReportApprovalView(discord.ui.View):
    def __init__(self, report_id: int, report_type: str):
        super().__init__(timeout=None)
        self.report_id = report_id
        self.report_type = report_type

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="report:approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_roles = [role.id for role in interaction.user.roles]
        if not any(role_id in member_roles for role_id in REPORT_ROLES):
            return await interaction.response.send_message("❌ You don't have permission to approve reports!", ephemeral=True)

        success = await approve_report(self.report_id, interaction.user.id)
        if not success:
            return await interaction.response.send_message("❌ This report has already been processed!", ephemeral=True)

        report = await get_report(self.report_id)
        data = report['data']

        if self.report_type == 'warpun':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Static ID:** {data['static_id']}\n"
                f"**3. Warn reason:** {data['reason']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "⚖️ Warn Removal Request"
            color = discord.Color.red()
        elif self.report_type == 'afk':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. AFK reason:** {data['reason']}\n"
                f"**3. Absence time:** {data['time']}"
            )
            title = "💤 AFK Report"
            color = discord.Color.blue()
        elif self.report_type == 'farmafk':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Chosen option:** {data['variant']}\n"
                f"**3. Leave period:** {data['period']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "📑 Farm AFK Report"
            color = discord.Color.purple()
        elif self.report_type == 'promote':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Current rank ➔ Applying for:** {data['rank']}\n"
                f"**3. Work completed:** {data['work']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "📈 Promotion Application"
            color = discord.Color.gold()
        else:  # contract
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Static ID:** {data['static_id']}\n"
                f"**3. What exactly?:** {data['what']}\n"
                f"**4. Required quantity:** {data['quantity']}\n"
                f"**5. Courier rank:** {data['rank']}"
            )
            title = "🌿 Contract Resource Request"
            color = discord.Color.green()

        e = discord.Embed(title=title, description=report_text, color=color)
        e.add_field(name="✅ Status", value=f"Approved by: {interaction.user.mention}", inline=False)

        if self.report_type == 'contract':
            amount_text = data['quantity']
            amount = int(''.join(filter(str.isdigit, amount_text)))
            resource_type = data['what'].lower()
            if 'green' in resource_type:
                resource_type = 'green'
            elif 'blue' in resource_type:
                resource_type = 'blue'
            elif 'white' in resource_type:
                resource_type = 'white'
            else:
                resource_type = 'green'

            await update_contract_stats(resource_type, amount)
            await add_contract_request(report['user_id'], report['user_name'], resource_type, amount)

            stats_channel_id = 1455238916440457326
            stats_channel = interaction.client.get_channel(stats_channel_id)
            if stats_channel:
                stats = await get_contract_stats()
                history = await get_contract_history(8)

                history_lines = []
                for entry in history:
                    emoji = "🟢" if entry['resource_type'] == 'green' else "🔵" if entry['resource_type'] == 'blue' else "⚪"
                    history_lines.append(f"{emoji} <@{entry['user_id']}> — {entry['amount']} pcs. ({entry['time_str']})")

                history_text = "\n".join(history_lines) if history_lines else "No records"

                stats_embed = discord.Embed(
                    title="📊 Resource Issuance Statistics",
                    color=discord.Color.from_rgb(13, 95, 92)
                )
                stats_embed.add_field(
                    name="📈 Total issued",
                    value=(
                        f"🟢 **Green:** {stats['green']} pcs.\n"
                        f"🔵 **Blue:** {stats['blue']} pcs.\n"
                        f"⚪ **White:** {stats['white']} pcs."
                    ),
                    inline=False
                )
                stats_embed.add_field(name="📋 Recent issuances", value=history_text, inline=False)
                stats_embed.set_footer(text="Cripsize FamQ • Resource Statistics")

                existing_msg = None
                async for message in stats_channel.history(limit=100):
                    if message.author == interaction.client.user and message.embeds:
                        embed = message.embeds[0]
                        if embed.title == "📊 Resource Issuance Statistics":
                            existing_msg = message
                            break

                view = ClearUserView()

                if existing_msg:
                    await existing_msg.edit(embed=stats_embed, view=view)
                else:
                    await stats_channel.send(embed=stats_embed, view=view)

        e.set_footer(text=f"Submitted by: {report['user_name']} | ID: {report['user_id']}")

        await interaction.message.edit(embed=e, view=None)
        await interaction.response.send_message("✅ Report approved!", ephemeral=True)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="report:reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_roles = [role.id for role in interaction.user.roles]
        if not any(role_id in member_roles for role_id in REPORT_ROLES):
            return await interaction.response.send_message("❌ You don't have permission to reject reports!", ephemeral=True)

        success = await reject_report(self.report_id, interaction.user.id)
        if not success:
            return await interaction.response.send_message("❌ This report has already been processed!", ephemeral=True)

        report = await get_report(self.report_id)
        data = report['data']

        if self.report_type == 'warpun':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Static ID:** {data['static_id']}\n"
                f"**3. Warn reason:** {data['reason']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "⚖️ Warn Removal Request"
            color = discord.Color.red()
        elif self.report_type == 'afk':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. AFK reason:** {data['reason']}\n"
                f"**3. Absence time:** {data['time']}"
            )
            title = "💤 AFK Report"
            color = discord.Color.blue()
        elif self.report_type == 'farmafk':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Chosen option:** {data['variant']}\n"
                f"**3. Leave period:** {data['period']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "📑 Farm AFK Report"
            color = discord.Color.purple()
        elif self.report_type == 'promote':
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Current rank ➔ Applying for:** {data['rank']}\n"
                f"**3. Work completed:** {data['work']}\n"
                f"**4. Proof:** {data['evidence']}"
            )
            title = "📈 Promotion Application"
            color = discord.Color.gold()
        else:  # contract
            report_text = (
                f"**1. Nickname:** {data['name']}\n"
                f"**2. Static ID:** {data['static_id']}\n"
                f"**3. What exactly?:** {data['what']}\n"
                f"**4. Required quantity:** {data['quantity']}\n"
                f"**5. Courier rank:** {data['rank']}"
            )
            title = "🌿 Contract Resource Request"
            color = discord.Color.green()

        e = discord.Embed(title=title, description=report_text, color=color)
        e.add_field(name="❌ Status", value=f"Rejected by: {interaction.user.mention}", inline=False)
        e.set_footer(text=f"Submitted by: {report['user_name']} | ID: {report['user_id']}")

        await interaction.message.edit(embed=e, view=None)
        await interaction.response.send_message("✅ Report rejected!", ephemeral=True)


class WarpunModal(discord.ui.Modal, title="Warn Removal"):
    name = discord.ui.TextInput(label="Your nickname", placeholder="First_Last", required=True, max_length=50)
    static_id = discord.ui.TextInput(label="Your static ID", placeholder="#0000", required=True, max_length=15)
    reason = discord.ui.TextInput(label="Warn reason", placeholder="What the warning was issued for", required=True, max_length=200)
    evidence = discord.ui.TextInput(label="Proof", placeholder="Screenshot of the family balance deposit", style=discord.TextStyle.paragraph, required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        report_data = {
            'name': self.name.value,
            'static_id': self.static_id.value,
            'reason': self.reason.value,
            'evidence': self.evidence.value
        }
        global_name = f"{interaction.user.name}#{interaction.user.discriminator}"
        report_id = await create_report('warpun', interaction.user.id, global_name, report_data)

        e = discord.Embed(title="⚖️ Warn Removal Request", description=(
            f"**1. Nickname:** {self.name.value}\n"
            f"**2. Static ID:** {self.static_id.value}\n"
            f"**3. Warn reason:** {self.reason.value}\n"
            f"**4. Proof:** {self.evidence.value}"
        ), color=discord.Color.red())
        e.add_field(name="⏳ Status", value="Pending approval", inline=False)
        e.set_footer(text=f"Submitted by: {global_name} | ID: {interaction.user.id}")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in REPORT_ROLES if interaction.guild.get_role(rid)])
        await interaction.channel.send(content=role_mentions if role_mentions else "", embed=e, view=ReportApprovalView(report_id, 'warpun'))
        await interaction.response.send_message("✅ Request submitted for approval!", ephemeral=True)


class AfkReportModal(discord.ui.Modal, title="AFK Report"):
    name = discord.ui.TextInput(label="Your nickname", placeholder="First_Last", required=True, max_length=50)
    reason = discord.ui.TextInput(label="AFK reason", placeholder="Rest / Study / Work / Personal circumstances", required=True, max_length=50)
    time = discord.ui.TextInput(label="Absence time", placeholder="Specify hours, e.g.: 14:00 to 22:00", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        report_data = {
            'name': self.name.value,
            'reason': self.reason.value,
            'time': self.time.value
        }
        global_name = f"{interaction.user.name}#{interaction.user.discriminator}"
        report_id = await create_report('afk', interaction.user.id, global_name, report_data)

        e = discord.Embed(title="💤 AFK Report", description=(
            f"**1. Nickname:** {self.name.value}\n"
            f"**2. AFK reason:** {self.reason.value}\n"
            f"**3. Absence time:** {self.time.value}"
        ), color=discord.Color.blue())
        e.add_field(name="⏳ Status", value="Pending approval", inline=False)
        e.set_footer(text=f"Submitted by: {global_name} | ID: {interaction.user.id}")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in REPORT_ROLES if interaction.guild.get_role(rid)])
        await interaction.channel.send(content=role_mentions if role_mentions else "", embed=e, view=ReportApprovalView(report_id, 'afk'))
        await interaction.response.send_message("✅ Report submitted for approval!", ephemeral=True)


class FarmAfkModal(discord.ui.Modal, title="Farm AFK Report"):
    name = discord.ui.TextInput(label="Your nickname", placeholder="First_Last", required=True, max_length=50)
    variant = discord.ui.TextInput(label="Chosen option", placeholder="Money / 10 MP / 20 Contracts", required=True, max_length=50)
    period = discord.ui.TextInput(label="Leave period", placeholder="from DD.MM to DD.MM", required=True, max_length=50)
    evidence = discord.ui.TextInput(label="Proof", placeholder="Attach screenshot to message", style=discord.TextStyle.paragraph, required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        report_data = {
            'name': self.name.value,
            'variant': self.variant.value,
            'period': self.period.value,
            'evidence': self.evidence.value
        }
        global_name = f"{interaction.user.name}#{interaction.user.discriminator}"
        report_id = await create_report('farmafk', interaction.user.id, global_name, report_data)

        e = discord.Embed(title="📑 Farm AFK Report", description=(
            f"**1. Nickname:** {self.name.value}\n"
            f"**2. Chosen option:** {self.variant.value}\n"
            f"**3. Leave period:** {self.period.value}\n"
            f"**4. Proof:** {self.evidence.value}"
        ), color=discord.Color.purple())
        e.add_field(name="⏳ Status", value="Pending approval", inline=False)
        e.set_footer(text=f"Submitted by: {global_name} | ID: {interaction.user.id}")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in REPORT_ROLES if interaction.guild.get_role(rid)])
        await interaction.channel.send(content=role_mentions if role_mentions else "", embed=e, view=ReportApprovalView(report_id, 'farmafk'))
        await interaction.response.send_message("✅ Report submitted for approval!", ephemeral=True)


class PromoteModal(discord.ui.Modal, title="Promotion Application"):
    name = discord.ui.TextInput(label="Your nickname", placeholder="First_Last", required=True, max_length=50)
    rank = discord.ui.TextInput(label="Current rank ➔ Applying for", placeholder="[2] Trainee ➔ [4] Verified", required=True, max_length=50)
    work = discord.ui.TextInput(label="Work completed", placeholder="Brief: 25 Drug Courier / Last Name / GG Rollback", required=True, max_length=200)
    evidence = discord.ui.TextInput(label="Proof", placeholder="Link to rollback or screenshots", style=discord.TextStyle.paragraph, required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        report_data = {
            'name': self.name.value,
            'rank': self.rank.value,
            'work': self.work.value,
            'evidence': self.evidence.value
        }
        global_name = f"{interaction.user.name}#{interaction.user.discriminator}"
        report_id = await create_report('promote', interaction.user.id, global_name, report_data)

        e = discord.Embed(title="📈 Promotion Application", description=(
            f"**1. Nickname:** {self.name.value}\n"
            f"**2. Current rank ➔ Applying for:** {self.rank.value}\n"
            f"**3. Work completed:** {self.work.value}\n"
            f"**4. Proof:** {self.evidence.value}"
        ), color=discord.Color.gold())
        e.add_field(name="⏳ Status", value="Pending approval", inline=False)
        e.set_footer(text=f"Submitted by: {global_name} | ID: {interaction.user.id}")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in REPORT_ROLES if interaction.guild.get_role(rid)])
        await interaction.channel.send(content=role_mentions if role_mentions else "", embed=e, view=ReportApprovalView(report_id, 'promote'))
        await interaction.response.send_message("✅ Application submitted for approval!", ephemeral=True)


class ContractModal(discord.ui.Modal, title="Contract Resource Request"):
    name = discord.ui.TextInput(label="Your nickname", placeholder="First_Last", required=True, max_length=50)
    static_id = discord.ui.TextInput(label="Your static ID", placeholder="#0000", required=True, max_length=15)
    what = discord.ui.TextInput(label="What exactly?", placeholder="Green, Blue, White", required=True, max_length=20)
    quantity = discord.ui.TextInput(label="Required quantity", placeholder="e.g.: 20 pieces", required=True, max_length=50)
    rank = discord.ui.TextInput(label="Your courier rank", placeholder="e.g.: 3", required=True, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        report_data = {
            'name': self.name.value,
            'static_id': self.static_id.value,
            'what': self.what.value,
            'quantity': self.quantity.value,
            'rank': self.rank.value
        }
        global_name = f"{interaction.user.name}#{interaction.user.discriminator}"
        report_id = await create_report('contract', interaction.user.id, global_name, report_data)

        e = discord.Embed(title="🌿 Contract Resource Request", description=(
            f"**1. Nickname:** {self.name.value}\n"
            f"**2. Static ID:** {self.static_id.value}\n"
            f"**3. What exactly?:** {self.what.value}\n"
            f"**4. Required quantity:** {self.quantity.value}\n"
            f"**5. Courier rank:** {self.rank.value}"
        ), color=discord.Color.green())
        e.add_field(name="⏳ Status", value="Pending approval", inline=False)
        e.set_footer(text=f"Submitted by: {global_name} | ID: {interaction.user.id}")

        role_mentions = " ".join([interaction.guild.get_role(rid).mention for rid in REPORT_ROLES if interaction.guild.get_role(rid)])
        await interaction.channel.send(content=role_mentions if role_mentions else "", embed=e, view=ReportApprovalView(report_id, 'contract'))
        await interaction.response.send_message("✅ Request submitted for approval!", ephemeral=True)


class WarpunView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Fill out form", style=discord.ButtonStyle.success, custom_id="warpun_form")
    async def form_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarpunModal())


class AfkReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Submit report", style=discord.ButtonStyle.success, custom_id="afk_report")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AfkReportModal())


class FarmAfkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Submit report", style=discord.ButtonStyle.success, custom_id="farm_afk_report")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FarmAfkModal())


class PromoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Submit application", style=discord.ButtonStyle.success, custom_id="promote_report")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PromoteModal())


class ContractView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Fill out form", style=discord.ButtonStyle.success, custom_id="contract_form")
    async def form_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContractModal())


class ClearUserModal(discord.ui.Modal, title="Clear User Resources"):
    user_input = discord.ui.TextInput(
        label="User ID or @mention",
        placeholder="123456789012345678 or @Queran",
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw_input = self.user_input.value.strip()
        user_id = None

        mention_match = re.match(r'<@!?(\d+)>', raw_input)
        if mention_match:
            user_id = int(mention_match.group(1))
        else:
            try:
                user_id = int(raw_input)
            except ValueError:
                return await interaction.response.send_message(
                    "❌ Invalid format! Enter a user ID or @mention.",
                    ephemeral=True
                )

        count = await clear_user_contracts(user_id)

        if count == 0:
            return await interaction.response.send_message(
                f"⚠️ User <@{user_id}> has no resource records to delete.",
                ephemeral=True
            )

        stats_channel_id = 1455238916440457326
        stats_channel = interaction.client.get_channel(stats_channel_id)
        if stats_channel:
            stats = await get_contract_stats()
            history = await get_contract_history(8)

            history_lines = []
            for entry in history:
                emoji = "🟢" if entry['resource_type'] == 'green' else "🔵" if entry['resource_type'] == 'blue' else "⚪"
                history_lines.append(f"{emoji} <@{entry['user_id']}> — {entry['amount']} pcs. ({entry['time_str']})")

            history_text = "\n".join(history_lines) if history_lines else "No records"

            stats_embed = discord.Embed(
                title="📊 Resource Issuance Statistics",
                color=discord.Color.from_rgb(13, 95, 92)
            )
            stats_embed.add_field(
                name="📈 Total issued",
                value=(
                    f"🟢 **Green:** {stats['green']} pcs.\n"
                    f"🔵 **Blue:** {stats['blue']} pcs.\n"
                    f"⚪ **White:** {stats['white']} pcs."
                ),
                inline=False
            )
            stats_embed.add_field(name="📋 Recent issuances", value=history_text, inline=False)
            stats_embed.set_footer(text="Cripsize FamQ • Resource Statistics")

            existing_msg = None
            async for message in stats_channel.history(limit=100):
                if message.author == interaction.client.user and message.embeds:
                    embed = message.embeds[0]
                    if embed.title == "📊 Resource Issuance Statistics":
                        existing_msg = message
                        break

            view = ClearUserView()

            if existing_msg:
                await existing_msg.edit(embed=stats_embed, view=view)
            else:
                await stats_channel.send(embed=stats_embed, view=view)

        await interaction.response.send_message(
            f"✅ Deleted {count} resource records for user <@{user_id}>!",
            ephemeral=True
        )


class ClearUserView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🧹 Clear user", style=discord.ButtonStyle.danger, custom_id="clear_user_button")
    async def clear_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_roles = [role.id for role in interaction.user.roles]
        if not any(role_id in member_roles for role_id in REPORT_ROLES):
            return await interaction.response.send_message(
                "❌ You don't have permission to clear contracts!",
                ephemeral=True
            )
        await interaction.response.send_modal(ClearUserModal())
