# 🤖 CRIPSIZE Discord Bot

<div align="center">

A powerful all-in-one Discord bot built for the **CRIPSIZE** family community.  
It combines moderation, applications, voting systems, temp voice channels, squad events, logging, anti-raid protection, and much more.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-%3E%3D2.3.0-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-07405e?style=for-the-badge&logo=sqlite&logoColor=white)

</div>

---

# ✨ Features

## 🛡️ Moderation
- Kick, ban, unban members
- Bulk message deletion
- Anti-spam auto timeout
- Anti-raid join protection
- Full moderation logging

## 📋 Applications
- Interactive family application system
- Recruiter review flow
- Accept / reject buttons
- Automatic result posting
- DM notifications for applicants

## 🗳️ Voting System
- Rank up/down votes
- Family warn/kick votes
- Live vote tracking
- Configurable quorum system

## 📊 Reports
- Warn removal requests
- AFK reports
- Farm AFK reports
- Promotion requests
- Contract resource requests

## 🔊 TempVoice System
- Auto-created voice channels
- Full GUI management panel
- Rename, limit, lock/unlock
- Invite, kick, ban users
- Transfer ownership
- RTC region control

## 🏟️ Squad Events
- `/pluse` event system
- Main and reserve roster slots
- MVP selection
- Check-in system
- Reminder buttons

## 📜 Audit Logging
- Message edits/deletes
- Role updates
- Voice activity
- Channel changes
- Ban/unban logs

## 🚫 Protection Systems
- Anti-spam detection
- Anti-raid join detection
- Automatic moderation actions

---

# 🚀 Getting Started

## 📦 Requirements

Before running the bot, make sure you have:

- **Python 3.10+**
- A Discord bot token
- Enabled privileged intents:
  - `GUILD_MEMBERS`
  - `MESSAGE_CONTENT`
  - `PRESENCE`

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/crip-bot-dc.git
cd crip-bot-dc
```

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install discord.py aiosqlite python-dotenv
```

---

## 3️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_bot_token_here
```

---

## 4️⃣ Configure `config.json`

Create or edit `config.json`:

```json
{
  "guild_id": 123456789012345678,
  "imm_role_id": 123456789012345678,

  "modlog_channel_id": 123456789012345678,
  "chronology_channel_id": 123456789012345678,

  "access_requests_channel_id": 123456789012345678,

  "application_channel_id": 123456789012345678,
  "application_result_channel_id": 123456789012345678,
  "waiting_room_channel_id": 123456789012345678,

  "tempvoice_category_id": 123456789012345678,
  "tempvoice_create_channel_id": 123456789012345678,

  "spam_msg_limit": 6,
  "spam_time_window": 8,
  "automute_seconds": 300,

  "raid_join_limit": 6,
  "raid_time_window": 20,
  "raid_timeout_seconds": 600
}
```

---

# ⚡ Run the Bot

```bash
python run.py
```

---

# 📁 Project Structure

```plaintext
crip-bot-dc/
│
├── run.py
├── config.json
├── .env
├── database.sqlite
│
├── banner.png
├── avatar.png
├── tempvoice_ui.png
│
└── bot/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── utils.py
    │
    ├── cogs/
    │   ├── general.py
    │   ├── moderation.py
    │   ├── events.py
    │   ├── logs.py
    │   ├── applications.py
    │   ├── voting.py
    │   ├── reports.py
    │   ├── tempvoice.py
    │   └── pluse.py
    │
    └── ui/
        ├── access.py
        ├── applications.py
        ├── voting.py
        ├── reports.py
        ├── tempvoice.py
        └── pluse.py
```

---

# 💬 Commands

## ℹ️ General

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/ui [user]` | Detailed user information |
| `/si` | Server statistics |
| `/ava [user]` | Show user avatar |
| `/banner [user]` | Show user banner |
| `/time [user]` | Account/server age |
| `/boosters` | List server boosters |
| `/guess [number]` | Guess mini-game |

---

## 🛡️ Moderation

| Command | Description |
|---|---|
| `/clear <amount>` | Delete messages |
| `/kick <user>` | Kick member |
| `/ban <user>` | Ban member |
| `/unban <user_id>` | Unban by ID |
| `/access [reason]` | Access request |

---

## 📊 Reports

| Command | Description |
|---|---|
| `/warn-template` | Warn removal form |
| `/afkreport` | AFK report |
| `/farmafk` | Farm AFK report |
| `/promote` | Promotion request |
| `/contract` | Contract request |
| `/afk_list` | Today's AFK list |

---

## 🗳️ Voting

| Command | Description |
|---|---|
| `/rangup <target>` | Promotion vote |
| `/rangdown <target>` | Demotion vote |
| `/famwarn <target>` | Warn vote |
| `/famkick <target>` | Kick vote |

---

## 🔊 TempVoice

| Command | Description |
|---|---|
| `/voicepanel` | Send voice panel |
| `/voice name <name>` | Rename channel |
| `/voice limit <0-99>` | Set user limit |
| `/voice lock` | Lock channel |
| `/voice unlock` | Unlock channel |
| `/voice invite <user>` | Invite member |
| `/voice kick <user>` | Kick member |
| `/voice ban <user>` | Ban member |
| `/voice unban <user>` | Unban member |
| `/voice region <region>` | Set RTC region |
| `/voice transfer <user>` | Transfer ownership |

---

## 🏟️ Events

| Command | Description |
|---|---|
| `/pluse` | Create squad event |
| `/mptag <msg>` | Triple @everyone ping |
| `/send_application_panel` | Send application panel |

---

# 🔒 Required Bot Permissions

The bot requires the following permissions:

- ✅ Manage Channels
- ✅ Kick Members
- ✅ Ban Members
- ✅ Moderate Members
- ✅ Manage Messages
- ✅ Manage Roles
- ✅ View Audit Log
- ✅ Move Members
- ✅ Mute Members
- ✅ Deafen Members
- ✅ Send Messages
- ✅ Embed Links
- ✅ Read Message History
- ✅ Use Application Commands
- ✅ Manage Nicknames

---

# 🗄️ Database

The bot uses **SQLite** with **aiosqlite**.

- Database file is automatically created on first startup
- Tables initialize automatically
- Persistent Discord views survive restarts
- Migration logic is handled in `bot/database.py`

---

# 🧩 Dependencies

```txt
discord.py >= 2.3.0
aiosqlite
python-dotenv
```

Install everything:

```bash
pip install discord.py aiosqlite python-dotenv
```

---

# 📄 License

This project is licensed under the terms of the `LICENSE` file.

---

## 📫 Contact

* **Email:** [bakalejkoandrij@gmail.com](mailto:bakalejkoandrij@gmail.com)
* **LinkedIn:** [linkedin.com/in/andrii-bakaleiko](https://linkedin.com/in/andrii-bakaleiko)
* **GitHub:** [github.com/bqquiet](https://github.com/bqquiet)

---

<div align="center">
  <b>made by <a href="https://github.com/bqquiet">bqquiet</a></b>
</div>
