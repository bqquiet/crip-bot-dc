import aiosqlite
import json
import datetime
from typing import Optional
from .config import DB_PATH, DATABASE_PATH
from .utils import now_ts
import random

async def init_contract_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS contract_stats (
                resource_type TEXT PRIMARY KEY,
                total_amount INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        for resource in ['green', 'blue', 'white']:
            await db.execute(
                'INSERT OR IGNORE INTO contract_stats (resource_type, total_amount) VALUES (?, 0)',
                (resource,)
            )
        await db.commit()

async def init_contract_history():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS contract_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def update_contract_stats(resource_type: str, amount: int) -> int:
    resource_type = resource_type.lower().strip()
    if resource_type not in ['green', 'blue', 'white']:
        return 0

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'UPDATE contract_stats SET total_amount = total_amount + ?, last_updated = CURRENT_TIMESTAMP WHERE resource_type = ?',
            (amount, resource_type)
        )
        await db.commit()

        cursor = await db.execute(
            'SELECT total_amount FROM contract_stats WHERE resource_type = ?',
            (resource_type,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_contract_stats() -> dict:
    stats = {'green': 0, 'blue': 0, 'white': 0}
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT resource_type, total_amount FROM contract_stats')
        rows = await cursor.fetchall()
        for resource_type, amount in rows:
            stats[resource_type.lower()] = amount
    return stats

async def add_contract_request(user_id: int, user_name: str, resource_type: str, amount: int):
    resource_type = resource_type.lower().strip()
    if resource_type not in ['green', 'blue', 'white']:
        return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.execute(
            'INSERT INTO contract_history (user_id, user_name, resource_type, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
            (user_id, user_name, resource_type, amount, timestamp)
        )
        await db.commit()

async def get_contract_history(limit: int = 10) -> list:
    history = []
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            'SELECT user_id, resource_type, amount, timestamp FROM contract_history ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        rows = await cursor.fetchall()
        for user_id, resource_type, amount, timestamp in rows:
            try:
                if timestamp:
                    if '.' in timestamp:
                        timestamp = timestamp.split('.')[0] + 'Z'
                    else:
                        timestamp = timestamp.replace(' ', 'T') + 'Z'

                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_ago = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()

                    if time_ago < 60:
                        time_str = f"{int(time_ago)} сек. назад"
                    elif time_ago < 3600:
                        time_str = f"{int(time_ago // 60)} мин. назад"
                    elif time_ago < 86400:
                        time_str = f"{int(time_ago // 3600)} ч. назад"
                    else:
                        time_str = dt.strftime('%d.%m.%Y')
                else:
                    time_str = "только что"
            except Exception as e:
                time_str = "—"

            history.append({
                'user_id': user_id,
                'resource_type': resource_type,
                'amount': amount,
                'time_str': time_str
            })
    return history

async def init_reports_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                data TEXT NOT NULL,
                approved_by INTEGER DEFAULT 0,
                approved_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def create_report(report_type: str, user_id: int, user_name: str, data: dict) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT INTO reports (report_type, user_id, user_name, data) VALUES (?, ?, ?, ?)',
            (report_type, user_id, user_name, json.dumps(data))
        )
        await db.commit()
        cursor = await db.execute('SELECT last_insert_rowid()')
        row = await cursor.fetchone()
        return row[0]

async def get_report(report_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'report_type': row[1],
            'user_id': row[2],
            'user_name': row[3],
            'data': json.loads(row[4]),
            'approved_by': row[5],
            'approved_at': row[6],
            'status': row[7],
            'created_at': row[8]
        }

async def approve_report(report_id: int, approver_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'UPDATE reports SET status = "approved", approved_by = ?, approved_at = CURRENT_TIMESTAMP WHERE id = ? AND status = "pending"',
            (approver_id, report_id)
        )
        await db.commit()
        cursor = await db.execute('SELECT changes()')
        changes = await cursor.fetchone()
        return changes[0] > 0

async def reject_report(report_id: int, rejector_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'UPDATE reports SET status = "rejected", approved_by = ? WHERE id = ? AND status = "pending"',
            (rejector_id, report_id)
        )
        await db.commit()
        cursor = await db.execute('SELECT changes()')
        changes = await cursor.fetchone()
        return changes[0] > 0

async def clear_user_contracts(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM contract_history WHERE user_id = ?', (user_id,))
        count = (await cursor.fetchone())[0]

        if count == 0:
            return 0

        await db.execute('DELETE FROM contract_history WHERE user_id = ?', (user_id,))

        for resource_type in ['green', 'blue', 'white']:
            cursor = await db.execute('SELECT SUM(amount) FROM contract_history WHERE resource_type = ?', (resource_type,))
            total = (await cursor.fetchone())[0] or 0
            await db.execute('UPDATE contract_stats SET total_amount = ? WHERE resource_type = ?', (total, resource_type))

        await db.commit()
        return count

async def init_voting_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS rank_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                target TEXT NOT NULL,
                action_type TEXT NOT NULL,
                command_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vote_id INTEGER NOT NULL,
                voter_id INTEGER NOT NULL,
                voter_name TEXT NOT NULL,
                vote TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vote_id) REFERENCES rank_votes (id)
            )
        ''')
        await db.commit()

async def migrate_voting_tables():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("PRAGMA table_info(votes)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'voter_name' not in column_names:
            await db.execute("ALTER TABLE votes ADD COLUMN voter_name TEXT NOT NULL DEFAULT 'Unknown'")
            await db.commit()

async def create_vote(guild_id: int, channel_id: int, message_id: int, author_id: int, author_name: str, target: str, action_type: str, command_type: str) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT INTO rank_votes (guild_id, channel_id, message_id, author_id, author_name, target, action_type, command_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (guild_id, channel_id, message_id, author_id, author_name, target, action_type, command_type)
        )
        await db.commit()
        cursor = await db.execute('SELECT last_insert_rowid()')
        row = await cursor.fetchone()
        return row[0]

async def add_vote(vote_id: int, voter_id: int, voter_name: str, vote: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT INTO votes (vote_id, voter_id, voter_name, vote) VALUES (?, ?, ?, ?)',
            (vote_id, voter_id, voter_name, vote)
        )
        await db.commit()

async def get_votes(vote_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT vote, COUNT(*) as count FROM votes WHERE vote_id = ? GROUP BY vote', (vote_id,))
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def get_voters(vote_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT voter_id, voter_name, vote FROM votes WHERE vote_id = ?', (vote_id,))
        return await cursor.fetchall()

async def close_vote(vote_id: int, status: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE rank_votes SET status = ? WHERE id = ?', (status, vote_id))
        await db.commit()

async def init_pluse_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pluse_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pluse_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_finished BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def save_pluse_vote(message_id: int, user_id: int, user_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO pluse_votes (message_id, user_id, user_name) VALUES (?, ?, ?)', (message_id, user_id, user_name))
        await db.commit()

async def get_pluse_votes(message_id: int) -> list:
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT user_id, user_name FROM pluse_votes WHERE message_id = ? ORDER BY voted_at ASC', (message_id,))
            return await cursor.fetchall()
    except Exception as e:
        print(f"Ошибка получения плюсов из БД: {e}")
        return []

async def save_pluse_message(message_id: int, channel_id: int, author_id: int, text: str, finished: bool = False):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO pluse_messages (message_id, channel_id, author_id, text, is_finished) VALUES (?, ?, ?, ?, ?)',
            (message_id, channel_id, author_id, text, int(finished))
        )
        await db.commit()

async def get_pluse_message(message_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT channel_id, author_id, text, is_finished FROM pluse_messages WHERE message_id = ?', (message_id,))
        row = await cursor.fetchone()
        if row:
            return {'channel_id': row[0], 'author_id': row[1], 'text': row[2], 'is_finished': bool(row[3])}
        return None

async def finish_pluse_message(message_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE pluse_messages SET is_finished = 1 WHERE message_id = ?', (message_id,))
        await db.commit()

import re
def parse_afk_end_time(time_str: str) -> Optional[datetime.datetime]:
    now = datetime.datetime.now(datetime.timezone.utc)
    match = re.search(r'с\s*(\d{1,2}:\d{2})\s*до\s*(\d{1,2}:\d{2})', time_str)
    if match:
        end_time = match.group(2)
        try:
            end_dt = datetime.datetime.combine(
                now.date(),
                datetime.datetime.strptime(end_time, '%H:%M').time(),
                tzinfo=datetime.timezone.utc
            )
            return end_dt
        except:
            pass
    match = re.search(r'(\d+)\s*час', time_str)
    if match:
        hours = int(match.group(1))
        return now + datetime.timedelta(hours=hours)
    return None

async def get_active_afk_reports():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT user_id, user_name, data, report_type
            FROM reports
            WHERE report_type IN ('afk', 'farmafk')
              AND status = 'approved'
              AND created_at >= datetime('now', 'utc', 'start of day')
        """)
        rows = await cursor.fetchall()
        active_reports = []
        for user_id, user_name, data_json, report_type in rows:
            data = json.loads(data_json)
            active_reports.append((user_id, user_name, data, report_type))
        return active_reports

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
CREATE TABLE IF NOT EXISTS xp (
guild_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
xp INTEGER NOT NULL DEFAULT 0,
last_msg_ts INTEGER NOT NULL DEFAULT 0,
voice_seconds INTEGER NOT NULL DEFAULT 0,
PRIMARY KEY (guild_id, user_id)
)
""")
        await db.execute("""
CREATE TABLE IF NOT EXISTS tempvoice (
guild_id INTEGER NOT NULL,
owner_id INTEGER NOT NULL,
channel_id INTEGER NOT NULL,
created_ts INTEGER NOT NULL,
PRIMARY KEY (guild_id, channel_id)
)
""")
        await db.execute("""
CREATE TABLE IF NOT EXISTS access_requests (
guild_id INTEGER NOT NULL,
msg_id INTEGER NOT NULL,
requester_id INTEGER NOT NULL,
created_ts INTEGER NOT NULL,
PRIMARY KEY (guild_id, msg_id)
)
""")
        await db.commit()

async def ensure_xp_row(guild_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO xp (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        await db.commit()

async def add_xp(guild_id: int, user_id: int, amount: int):
    await ensure_xp_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE xp SET xp = xp + ? WHERE guild_id=? AND user_id=?", (amount, guild_id, user_id))
        await db.commit()

async def get_xp(guild_id: int, user_id: int) -> int:
    await ensure_xp_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT xp FROM xp WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = await cur.fetchone()
        return row[0]

async def set_last_msg_ts(guild_id: int, user_id: int, ts: int):
    await ensure_xp_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE xp SET last_msg_ts=? WHERE guild_id=? AND user_id=?", (ts, guild_id, user_id))
        await db.commit()

async def get_last_msg_ts(guild_id: int, user_id: int) -> int:
    await ensure_xp_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT last_msg_ts FROM xp WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = await cur.fetchone()
        return row[0]

async def add_voice_seconds(guild_id: int, user_id: int, seconds: int):
    await ensure_xp_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE xp SET voice_seconds = voice_seconds + ? WHERE guild_id=? AND user_id=?", (seconds, guild_id, user_id))
        await db.commit()

async def tv_get_owner(guild_id: int, channel_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT owner_id FROM tempvoice WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
        row = await cur.fetchone()
        return row[0] if row else None

async def tv_set(guild_id: int, owner_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO tempvoice (guild_id, owner_id, channel_id, created_ts) VALUES (?,?,?,?)", (guild_id, owner_id, channel_id, now_ts()))
        await db.commit()

async def tv_delete(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tempvoice WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
        await db.commit()

async def process_message_xp(guild_id: int, user_id: int, cooldown: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO xp (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))

        cur = await db.execute("SELECT last_msg_ts FROM xp WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = await cur.fetchone()
        last_ts = row[0] if row else 0
        now = now_ts()

        if now - last_ts >= cooldown:
            gain = random.randint(8, 15)
            await db.execute(
                "UPDATE xp SET xp = xp + ?, last_msg_ts = ? WHERE guild_id=? AND user_id=?", 
                (gain, now, guild_id, user_id)
            )
        await db.commit()