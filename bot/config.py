import os
import json
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = "config.json"
DB_PATH = "database.sqlite"
DATABASE_PATH = "database.sqlite"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()

def cfg_int(key: str, default=None) -> int:
    v = config.get(key, default)
    if v is None or v == "":
        if default is not None:
            return default
        raise RuntimeError(f"config.json: missing required key '{key}'")
    return int(v)

GUILD_ID = cfg_int("guild_id", 0)
IMM_ROLE_ID = cfg_int("imm_role_id", 0)
MODLOG_CHANNEL_ID = cfg_int("modlog_channel_id", 0)
CHRONOLOGY_CHANNEL_ID = cfg_int("chronology_channel_id", 0)
ACCESS_REQUESTS_CHANNEL_ID = cfg_int("access_requests_channel_id", 0)
APPLICATION_CHANNEL_ID = cfg_int("application_channel_id", 0)
APPLICATION_RESULT_CHANNEL_ID = cfg_int("application_result_channel_id", 0)
WAITING_ROOM_CHANNEL_ID = cfg_int("waiting_room_channel_id", 0)
APPLICATION_PANEL_IMAGE_URL = str(config.get("application_panel_image_url", "https://i.imgur.com/placeholder1.png"))
APPLICATION_RESULT_IMAGE_URL = str(config.get("application_result_image_url", "https://i.imgur.com/placeholder2.png"))
TEMPVOICE_CATEGORY_ID = cfg_int("tempvoice_category_id", 0)
TEMPVOICE_CREATE_CHANNEL_ID = cfg_int("tempvoice_create_channel_id", 0)

TEMPVOICE_UI_IMAGE = str(config.get("tempvoice_ui_image", "tempvoice_ui.png"))

SPAM_MSG_LIMIT = int(config.get("spam_msg_limit", 6))
SPAM_TIME_WINDOW = int(config.get("spam_time_window", 8))
AUTOMUTE_SECONDS = int(config.get("automute_seconds", 300))
RAID_JOIN_LIMIT = int(config.get("raid_join_limit", 6))
RAID_TIME_WINDOW = int(config.get("raid_time_window", 20))
RAID_TIMEOUT_SECONDS = int(config.get("raid_timeout_seconds", 600))
XP_COOLDOWN_SECONDS = 5

GUILD_OBJ = discord.Object(id=GUILD_ID) if GUILD_ID else None
EMBED_COLOR_MAIN = discord.Color.from_rgb(184, 124, 124)

REPORT_ROLES = [1450523148905873608, 1450523147660165322, 1450523145931985109]
VOTING_ROLES = [1450523144526889144, 1450523145931985109]
