import discord
from discord.ext import commands
import aiosqlite
from bot.config import TOKEN, GUILD_OBJ, GUILD_ID, DATABASE_PATH, config
from bot.database import (
    init_pluse_db, init_reports_db, init_voting_db, migrate_voting_tables,
    init_contract_stats, init_contract_history, db_init
)
from bot.ui import (
    TempVoicePanel, PluseView, WarpunView, AfkReportView, FarmAfkView,
    PromoteView, ContractView, ClearUserView, RankVoteView,
    ApplicationPanelView, ApplicationReviewView, ApplicationNewView
)

class ImmortalBot(commands.Bot):
    async def setup_hook(self) -> None:
        await db_init()
        await init_pluse_db()
        await init_reports_db()
        await init_voting_db()
        await migrate_voting_tables()
        await init_contract_stats()
        await init_contract_history()

        self.add_view(TempVoicePanel())
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pluse_messages'")
            if await cursor.fetchone():
                cursor = await db.execute('SELECT message_id, channel_id, author_id, text, is_finished FROM pluse_messages')
                rows = await cursor.fetchall()
                for message_id, channel_id, author_id, text, is_finished in rows:
                    data = {
                        'название': text,
                        'дата_text': '—',
                        'слоты': 35,
                        'роли': None,
                        'доп_слоты': None,
                        'комментарий': None,
                        'author_id': author_id,
                        'author_mention': f'<@{author_id}>',
                        'members': [],
                        'доп_members': [],
                        'moderators': [],
                        'marked': [],
                        'mvp_id': None,
                        'mvp_mention': None,
                        'image_url': None,
                        'finished': bool(is_finished),
                    }
                    view = PluseView(data)
                    self.add_view(view, message_id=message_id)

        self.add_view(WarpunView())
        self.add_view(AfkReportView())
        self.add_view(FarmAfkView())
        self.add_view(PromoteView())
        self.add_view(ContractView())
        self.add_view(ClearUserView())
        self.add_view(RankVoteView(0, "", "", "", 0, ""))
        self.add_view(ApplicationPanelView())
        self.add_view(ApplicationNewView())
        self.add_view(ApplicationReviewView())

        await self.load_extension("bot.cogs.general")
        await self.load_extension("bot.cogs.moderation")
        await self.load_extension("bot.cogs.tempvoice")
        await self.load_extension("bot.cogs.reports")
        await self.load_extension("bot.cogs.voting")
        await self.load_extension("bot.cogs.pluse")
        await self.load_extension("bot.cogs.events")
        await self.load_extension("bot.cogs.applications")
        await bot.load_extension("bot.cogs.logs")

        try:
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} глобальных слэш-команд")
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.voice_states = True
intents.presences = True
intents.moderation = True

bot = ImmortalBot(command_prefix=config.get('prefix', '.'), intents=intents)

def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing (.env).")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()