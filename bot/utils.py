import time as pytime
import datetime
import discord
import re
from typing import Optional
from .config import EMBED_COLOR_MAIN, GUILD_ID

def now_ts() -> int:
    return int(pytime.time())

def dt_en() -> str:
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

# Keep dt_ru as alias for compatibility
dt_ru = dt_en

def mention(u: discord.abc.User) -> str:
    return f"{u.mention} (`{u.id}`)"

async def get_guild(bot) -> Optional[discord.Guild]:
    return bot.get_guild(GUILD_ID)

async def ch_by_id(bot, ch_id: int) -> Optional[discord.abc.GuildChannel]:
    g = await get_guild(bot)
    if not g:
        return None
    return g.get_channel(ch_id)

async def send_modlog(bot, embed: discord.Embed):
    from .config import MODLOG_CHANNEL_ID
    if embed.color is None:
        embed.color = EMBED_COLOR_MAIN
    ch = await ch_by_id(bot, MODLOG_CHANNEL_ID)
    if isinstance(ch, discord.TextChannel):
        await ch.send(embed=embed)

async def send_chronology(bot, embed: discord.Embed):
    from .config import CHRONOLOGY_CHANNEL_ID
    if embed.color is None:
        embed.color = EMBED_COLOR_MAIN
    ch = await ch_by_id(bot, CHRONOLOGY_CHANNEL_ID)
    if isinstance(ch, discord.TextChannel):
        await ch.send(embed=embed)

async def timeout_member(member: discord.Member, seconds: int, reason: str):
    try:
        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
    except:
        pass

async def is_tv_owner(member: discord.Member, channel: discord.VoiceChannel) -> bool:
    from .database import tv_get_owner
    owner_id = await tv_get_owner(member.guild.id, channel.id)
    return owner_id == member.id

async def is_tempvoice_channel(channel: discord.VoiceChannel) -> bool:
    if not channel.guild:
        return False
    from .database import tv_get_owner
    owner_id = await tv_get_owner(channel.guild.id, channel.id)
    return owner_id is not None

USER_MENTION_RE = re.compile(r"<@!?(?P<id>\d+)>$")
async def _parse_member(guild: discord.Guild, raw: str) -> Optional[discord.Member]:
    raw = (raw or "").strip()
    if not raw:
        return None
    m = USER_MENTION_RE.match(raw)
    if m:
        uid = int(m.group("id"))
    else:
        try:
            uid = int(raw)
        except ValueError:
            raw_low = raw.lower()
            for mem in guild.members:
                if mem.name.lower() == raw_low or mem.display_name.lower() == raw_low:
                    return mem
            return None
    return guild.get_member(uid) or await guild.fetch_member(uid)

def _gold_warn_embed(title: str, desc: str) -> discord.Embed:
    return discord.Embed(title=title, description=desc, color=EMBED_COLOR_MAIN)

STATUS_MAP = {
    discord.Status.online: ("Online", "🟢"),
    discord.Status.idle: ("Idle", "🟡"),
    discord.Status.dnd: ("Do Not Disturb", "🔴"),
    discord.Status.offline: ("Offline", "⚫"),
}

def fmt_dt(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return "—"
    return dt.astimezone(datetime.timezone.utc).strftime("%d.%m.%Y")

def fmt_timedelta(delta: datetime.timedelta) -> str:
    total = int(delta.total_seconds())
    if total < 0:
        total = 0
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return ", ".join(parts)

def set_footer_ru(e: discord.Embed, interaction: discord.Interaction, *, include_user: bool = True, copyright_text: Optional[str] = None) -> None:
    parts = []
    if include_user:
        parts.append(f"Requested by: {interaction.user}")
    if copyright_text:
        parts.append(copyright_text)
    e.set_footer(text=' • '.join(parts))

def detect_device(m: discord.Member) -> str:
    try:
        if getattr(m, 'desktop_status', None) and m.desktop_status != discord.Status.offline:
            return "Desktop"
        if getattr(m, 'mobile_status', None) and m.mobile_status != discord.Status.offline:
            return "Mobile"
        if getattr(m, 'web_status', None) and m.web_status != discord.Status.offline:
            return "Browser"
    except Exception:
        pass
    return "—"

def make_embed(title: str, description: Optional[str] = None, *, color: Optional[discord.Color] = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=(color or EMBED_COLOR_MAIN),
    )

async def make_ui_embed(bot: discord.Client, interaction: discord.Interaction, member: discord.Member) -> discord.Embed:
    u = await bot.fetch_user(member.id)
    status_text, status_emoji = STATUS_MAP.get(member.status, (str(member.status), "⚪"))
    e = make_embed(title=f"Member Info: {member}")
    e.add_field(name="General:", value="​", inline=False)
    e.add_field(name="Username:", value=f"👤 {member}", inline=True)
    dev = detect_device(member)
    dev_emoji = {"Desktop": "🖥️", "Mobile": "📱", "Browser": "🌐"}.get(dev, "—")
    e.add_field(name="Device:", value=f"{dev_emoji} {dev}", inline=True)
    e.add_field(name="Status:", value=f"{status_emoji} {status_text}", inline=True)
    e.add_field(name="Display Name:", value=f"🧑‍💼 {member.display_name}", inline=False)
    top_role = getattr(member, 'top_role', None)
    e.add_field(name="Top Role:", value=(top_role.mention if top_role and top_role.name != '@everyone' else '—'), inline=False)
    joined = getattr(member, 'joined_at', None)
    now = datetime.datetime.now(datetime.timezone.utc)
    join_age = (now - joined) if joined else None
    acc_age = now - member.created_at
    e.add_field(name="Joined:", value=f"{fmt_dt(joined)}\n⏱️ ({fmt_timedelta(join_age) if join_age else '—'})", inline=True)
    e.add_field(name="Registered:", value=f"{fmt_dt(member.created_at)}\n⏳ ({fmt_timedelta(acc_age)})", inline=True)
    e.add_field(name="ID:", value=f"🆔 `{member.id}`", inline=False)
    badges: list[str] = []
    try:
        flags = getattr(u, 'public_flags', None)
        if flags:
            mapping = [
                ('staff', '🛡️'),
                ('partner', '🤝'),
                ('discord_certified_moderator', '🛡️'),
                ('hypesquad', '🎉'),
                ('hypesquad_bravery', '🦁'),
                ('hypesquad_brilliance', '🦄'),
                ('hypesquad_balance', '🌙'),
                ('bug_hunter_level_1', '🐛'),
                ('bug_hunter_level_2', '🐞'),
                ('early_supporter', '💎'),
                ('verified_bot_developer', '👨‍💻'),
                ('active_developer', '🔧'),
            ]
            for attr, emo in mapping:
                if getattr(flags, attr, False):
                    badges.append(emo)
        if getattr(member, 'premium_since', None):
            badges.append('✨')
        if member.bot:
            badges.append('🤖')
    except Exception:
        pass
    e.add_field(name='Badges:', value=(' '.join(badges) if badges else '—'), inline=False)
    custom_text = "—"
    try:
        for act in getattr(member, 'activities', []) or []:
            if getattr(act, 'type', None) == discord.ActivityType.custom:
                emoji = getattr(act, 'emoji', None)
                name = getattr(act, 'name', None) or ""
                custom_text = f"{emoji} {name}".strip() if emoji else (name.strip() or "—")
                break
    except Exception:
        pass
    e.add_field(name="Custom Status:", value=custom_text, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    if getattr(u, 'banner', None):
        try:
            e.set_image(url=u.banner.url)
        except Exception:
            pass
    set_footer_ru(e, interaction)
    return e

async def make_si_embed(interaction: discord.Interaction) -> discord.Embed:
    g = interaction.guild
    e = make_embed(title=f"Server Info: {g.name if g else '—'}")
    if not g:
        e.description = "❌ This command is only available in a server."
        set_footer_ru(e, interaction)
        return e
    e.add_field(name="General:", value="​", inline=False)
    e.add_field(name="Name:", value=f"🏷️ {g.name}", inline=True)
    e.add_field(name="ID:", value=f"`{g.id}`", inline=True)
    e.add_field(name="Owner:", value=(getattr(g, 'owner', None).mention if getattr(g, 'owner', None) else '—'), inline=True)
    channels = len(g.channels)
    roles = len(g.roles)
    e.add_field(name='Channels:', value=f'🟦 {channels}', inline=True)
    e.add_field(name='Roles:', value=f'💚 {roles}', inline=True)
    e.add_field(name='Members:', value=f'👥 {g.member_count}', inline=True)
    boosts = getattr(g, 'premium_subscription_count', 0) or 0
    tier = getattr(g, 'premium_tier', 0)
    e.add_field(name='Boosts:', value=f'🚀 {boosts}', inline=True)
    e.add_field(name='Boost Level:', value=f'⭐ {tier}', inline=True)
    e.add_field(name="Created:", value=f"📅 {fmt_dt(g.created_at)}", inline=True)
    if g.icon:
        e.set_thumbnail(url=g.icon.url)
    set_footer_ru(e, interaction)
    return e

def format_relative_time(delta: datetime.timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    years, remainder = divmod(total_seconds, 31536000)
    months, remainder = divmod(remainder, 2592000)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}mo")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return ", ".join(parts)
