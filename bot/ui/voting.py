import discord
from bot.config import VOTING_ROLES
from bot.database import get_votes, get_voters, close_vote, add_vote

class RankVoteView(discord.ui.View):
    def __init__(self, vote_id: int, target: str, action_type: str, command_type: str, author_id: int, author_name: str):
        super().__init__(timeout=None)
        self.vote_id = vote_id
        self.target = target
        self.action_type = action_type
        self.command_type = command_type
        self.author_id = author_id
        self.author_name = author_name
        self.message = None

    async def update_embed(self):
        votes = await get_votes(self.vote_id)
        voters = await get_voters(self.vote_id)

        yes_count = votes.get('yes', 0)
        no_count = votes.get('no', 0)
        total = yes_count + no_count

        if self.command_type == 'rangup':
            color = discord.Color.from_rgb(50, 150, 50)
        elif self.command_type == 'rangdown':
            color = discord.Color.from_rgb(200, 150, 50)
        elif self.command_type == 'famwarn':
            color = discord.Color.from_rgb(255, 200, 50)
        else:
            color = discord.Color.from_rgb(200, 50, 50)

        voters_text = []
        for voter_id, _, vote in voters:
            emoji = "✅" if vote == "yes" else "❌"
            voters_text.append(f"{emoji} <@{voter_id}>")

        voters_display = "\n".join(voters_text) if voters_text else "—"

        status_emoji = "⏳" if total < 4 else ("✅" if yes_count > no_count else "❌")
        status_text = "Active" if total < 4 else ("Approved" if yes_count > no_count else "Rejected")

        e = discord.Embed(
            title=f"🗳️ Vote: {self.action_type}",
            description=(
                f"**Target:** {self.target}\n\n"
                f"📊 **Results:**\n"
                f"✅ For: **{yes_count}**\n"
                f"❌ Against: **{no_count}**\n"
                f"👥 Voted: **{total}/4**\n\n"
                f"👥 **Voters:**\n{voters_display}"
            ),
            color=color
        )
        e.set_footer(text=f"Requested by: {self.author_name} | ID: {self.author_id} • {status_emoji} {status_text}")

        if total >= 4:
            await close_vote(self.vote_id, 'approved' if yes_count > no_count else 'rejected')
            await self.send_results(yes_count, no_count, voters)
            self.clear_items()

        if self.message:
            await self.message.edit(embed=e, view=self if total < 4 else None)

    async def send_results(self, yes_count: int, no_count: int, voters: list):
        if self.command_type == 'rangup':
            if yes_count > no_count:
                color = discord.Color.from_rgb(0, 200, 0)
                result_emoji = "✅"
                result_text = "VOTE PASSED"
                action_text = f"Player **{self.target}** has been successfully **promoted**!"
                footer_text = "Decision: Promotion approved by majority"
            else:
                color = discord.Color.from_rgb(200, 0, 0)
                result_emoji = "❌"
                result_text = "VOTE REJECTED"
                action_text = f"Player **{self.target}** was **NOT promoted**."
                footer_text = "Decision: Promotion rejected by majority"
        elif self.command_type == 'rangdown':
            if yes_count > no_count:
                color = discord.Color.from_rgb(0, 200, 0)
                result_emoji = "✅"
                result_text = "VOTE PASSED"
                action_text = f"Player **{self.target}** has been successfully **demoted**!"
                footer_text = "Decision: Demotion approved by majority"
            else:
                color = discord.Color.from_rgb(200, 0, 0)
                result_emoji = "❌"
                result_text = "VOTE REJECTED"
                action_text = f"Player **{self.target}** was **NOT demoted**."
                footer_text = "Decision: Demotion rejected by majority"
        elif self.command_type == 'famwarn':
            if yes_count > no_count:
                color = discord.Color.from_rgb(0, 200, 0)
                result_emoji = "✅"
                result_text = "VOTE PASSED"
                action_text = f"Player **{self.target}** has been successfully **warned**!"
                footer_text = "Decision: Warning approved by majority"
            else:
                color = discord.Color.from_rgb(200, 0, 0)
                result_emoji = "❌"
                result_text = "VOTE REJECTED"
                action_text = f"Player **{self.target}** was **NOT warned**."
                footer_text = "Decision: Warning rejected by majority"
        else:
            if yes_count > no_count:
                color = discord.Color.from_rgb(0, 200, 0)
                result_emoji = "✅"
                result_text = "VOTE PASSED"
                action_text = f"Player **{self.target}** has been successfully **kicked from the family**!"
                footer_text = "Decision: Kick approved by majority"
            else:
                color = discord.Color.from_rgb(200, 0, 0)
                result_emoji = "❌"
                result_text = "VOTE REJECTED"
                action_text = f"Player **{self.target}** was **NOT kicked** from the family."
                footer_text = "Decision: Kick rejected by majority"

        votes_detail = []
        for voter_id, _, vote in voters:
            emoji = "✅" if vote == "yes" else "❌"
            votes_detail.append(f"{emoji} <@{voter_id}>")

        votes_display = "\n".join(votes_detail)

        e = discord.Embed(
            title=f"{result_emoji} {result_text}",
            description=(
                f"**🎯 Target:** {self.target}\n"
                f"**📋 Type:** {self.action_type}\n\n"
                f"**📊 Vote results:**\n"
                f"✅ For: **{yes_count}**\n"
                f"❌ Against: **{no_count}**\n"
                f"👥 Total voted: **4/4**\n\n"
                f"**🗳️ Vote details:**\n{votes_display}\n\n"
                f"**⭐ Decision:**\n{action_text}"
            ),
            color=color
        )
        e.set_thumbnail(url="https://cdn.discordapp.com/attachments/861654715745697824/1465834268294123664/Gemini_Generated_Image_6ridj6ridj6ridj6.png?ex=69831dcb&is=6981cc4b&hm=49129df78e334933a166e36ac0bd3dfd4dc437c8b054d40c9fc0505ef10a107f&")
        e.set_footer(text=footer_text)

        if self.message:
            await self.message.channel.send(embed=e)

    @discord.ui.button(label="✅ For", style=discord.ButtonStyle.success, custom_id="vote_yes")
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in VOTING_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message("❌ You don't have permission to vote!", ephemeral=True)

        voters = await get_voters(self.vote_id)
        if any(voter_id == interaction.user.id for voter_id, _, _ in voters):
            return await interaction.response.send_message("❌ You have already voted!", ephemeral=True)

        await add_vote(self.vote_id, interaction.user.id, interaction.user.name, 'yes')
        await self.update_embed()
        await interaction.response.send_message("✅ Your vote has been counted!", ephemeral=True)

    @discord.ui.button(label="❌ Against", style=discord.ButtonStyle.danger, custom_id="vote_no")
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in VOTING_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message("❌ You don't have permission to vote!", ephemeral=True)

        voters = await get_voters(self.vote_id)
        if any(voter_id == interaction.user.id for voter_id, _, _ in voters):
            return await interaction.response.send_message("❌ You have already voted!", ephemeral=True)

        await add_vote(self.vote_id, interaction.user.id, interaction.user.name, 'no')
        await self.update_embed()
        await interaction.response.send_message("✅ Your vote has been counted!", ephemeral=True)
