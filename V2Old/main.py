import discord
from discord.ext import commands, tasks
import hashlib
import time
import sqlite3
import aiohttp
from wcwidth import wcswidth
import asyncio
import ssl
import os
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
from colorama import Fore, Style, init
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

conn = sqlite3.connect('gift_db.sqlite')
print(Fore.GREEN + "Database connection established successfully." + Style.RESET_ALL)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (fid INTEGER PRIMARY KEY, nickname TEXT, furnace_lv INTEGER DEFAULT 0)''')
conn.execute('''CREATE TABLE IF NOT EXISTS gift_codes (giftcode TEXT PRIMARY KEY, date TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS user_giftcodes (fid INTEGER, giftcode TEXT, status TEXT, PRIMARY KEY(fid, giftcode))''')
c.execute('''CREATE TABLE IF NOT EXISTS custom_commands (id INTEGER PRIMARY KEY AUTOINCREMENT, command_name TEXT NOT NULL, command_access TEXT NOT NULL, delete_message TEXT NOT NULL, action_type TEXT NOT NULL, action_message TEXT, action_gif TEXT, action_fixed_message TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY)''')
c.execute('''
    CREATE TABLE IF NOT EXISTS nickname_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fid INTEGER,
        old_nickname TEXT,
        new_nickname TEXT,
        change_date TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS furnace_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fid INTEGER,
        old_furnace_lv INTEGER,
        new_furnace_lv INTEGER,
        change_date TEXT
    )
''')
conn.commit()
bot.conn = conn

level_mapping = {
    31: "30-1", 32: "30-2", 33: "30-3", 34: "30-4",
    35: "FC 1", 36: "FC 1 - 1", 37: "FC 1 - 2", 38: "FC 1 - 3", 39: "FC 1 - 4",
    40: "FC 2", 41: "FC 2 - 1", 42: "FC 2 - 2", 43: "FC 2 - 3", 44: "FC 2 - 4",
    45: "FC 3", 46: "FC 3 - 1", 47: "FC 3 - 2", 48: "FC 3 - 3", 49: "FC 3 - 4",
    50: "FC 4", 51: "FC 4 - 1", 52: "FC 4 - 2", 53: "FC 4 - 3", 54: "FC 4 - 4",
    55: "FC 5", 56: "FC 5 - 1", 57: "FC 5 - 2", 58: "FC 5 - 3", 59: "FC 5 - 4",
    60: "FC 6", 61: "FC 6 - 1", 62: "FC 6 - 2", 63: "FC 6 - 3", 64: "FC 6 - 4",
    65: "FC 7", 66: "FC 7 - 1", 67: "FC 7 - 2", 68: "FC 7 - 3", 69: "FC 7 - 4",
    70: "FC 8", 71: "FC 8 - 1", 72: "FC 8 - 2", 73: "FC 8 - 3", 74: "FC 8 - 4",
    75: "FC 9", 76: "FC 9 - 1", 77: "FC 9 - 2", 78: "FC 9 - 3", 79: "FC 9 - 4",
    80: "FC 10", 81: "FC 10 - 1", 82: "FC 10 - 2", 83: "FC 10 - 3", 84: "FC 10 - 4"
}

def load_settings():
    default_settings = {
        'BOT_TOKEN': '',
        'SECRET': 'tB87#kPtkxqOS2',
        'CHANNEL_ID': '1111',
        'ALLIANCE_NAME': 'RELOISBACK',
        'UPDATE_INTERVAL': '20'
    }

    if not os.path.exists('settings.txt'):
        with open('settings.txt', 'w') as f:
            for key, value in default_settings.items():
                f.write(f"{key}={value}\n")

        print(Fore.GREEN + "settings.txt file has been created. Please fill in the file and restart the program." + Style.RESET_ALL)
        exit()

    settings = {}
    with open('settings.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                settings[key] = value

    for key in default_settings:
        if not settings.get(key):
            print(Fore.GREEN + f"{key} is missing from settings.txt. Please check the file." + Style.RESET_ALL)
            exit()

    settings['UPDATE_INTERVAL'] = int(settings['UPDATE_INTERVAL'])

    if 'ADMIN' in settings and settings['ADMIN']:
        settings['ADMIN'] = [int(admin_id.strip()) for admin_id in settings['ADMIN'].split(",")]
    else:
        settings['ADMIN'] = []

    return settings

settings = load_settings()
update_interval = settings['UPDATE_INTERVAL']
BOT_TOKEN = settings['BOT_TOKEN']
SECRET = settings['SECRET']
CHANNEL_ID = int(settings['CHANNEL_ID'])
ALLIANCE_NAME = settings['ALLIANCE_NAME']
bot.SECRET = settings['SECRET']
bot.ALLIANCE_NAME = settings['ALLIANCE_NAME']

async def fetch_user_data(fid):
    url = 'https://wos-giftcode-api.centurygame.com/api/player'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    current_time = int(time.time() * 1000)
    form = f"fid={fid}&time={current_time}"
    sign = hashlib.md5((form + SECRET).encode('utf-8')).hexdigest()
    form = f"sign={sign}&{form}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=form, ssl=False) as response:
            return await response.json() if response.status == 200 else response.status

async def check_agslist(channel):
    print(Fore.GREEN + "The control started..." + Style.RESET_ALL)
    c.execute("SELECT fid, nickname, furnace_lv FROM users")
    users = c.fetchall()
    
    furnace_changes, nickname_changes = [], []

    for fid, old_nickname, old_furnace_lv in users:
        while True:
            data = await fetch_user_data(fid)
            if isinstance(data, dict):
                new_furnace_lv = data['data']['stove_lv']
                new_nickname = data['data']['nickname'].strip()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_furnace_display = level_mapping.get(new_furnace_lv, new_furnace_lv) if new_furnace_lv >= 30 else new_furnace_lv
                old_furnace_display = level_mapping.get(old_furnace_lv, old_furnace_lv) if old_furnace_lv >= 30 else old_furnace_lv

                if new_furnace_lv != old_furnace_lv:
                    c.execute(
                        "INSERT INTO furnace_changes (fid, old_furnace_lv, new_furnace_lv, change_date) VALUES (?, ?, ?, ?)",
                        (fid, old_furnace_lv, new_furnace_lv, current_time)
                    )
                    conn.commit()
                    c.execute("UPDATE users SET furnace_lv = ? WHERE fid = ?", (new_furnace_lv, fid))
                    conn.commit()
                    furnace_changes.append(f"{old_nickname}: {old_furnace_display} -> {new_furnace_display}")

                if new_nickname.lower() != old_nickname.lower().strip():
                    c.execute(
                        "INSERT INTO nickname_changes (fid, old_nickname, new_nickname, change_date) VALUES (?, ?, ?, ?)",
                        (fid, old_nickname, new_nickname, current_time)
                    )
                    conn.commit()
                    c.execute("UPDATE users SET nickname = ? WHERE fid = ?", (new_nickname, fid))
                    conn.commit()
                    nickname_changes.append(f"{old_nickname} -> {new_nickname}")

                break
            elif data == 429:
                await asyncio.sleep(60)
            else:
                await channel.send(f"Error fetching data for user with ID {fid}. API response: {data}")
                break

    if furnace_changes:
        await send_embed(channel, "Furnace Level Changes", "\n".join(furnace_changes), discord.Color.orange())
    if nickname_changes:
        await send_embed(channel, "Nickname Changes", "\n".join(nickname_changes), discord.Color.blue())
    if not (furnace_changes or nickname_changes):
        print(Fore.GREEN + "No change." + Style.RESET_ALL)

    print(Fore.GREEN + "Control over!" + Style.RESET_ALL)

async def send_embed(channel, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    await channel.send(embed=embed)

async def send_embed(channel, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="[Reloisback](https://dc.gg/whiteoutall)")
    await channel.send(embed=embed)

@tasks.loop(minutes=settings['UPDATE_INTERVAL'])
async def auto_update_agslist():
    channel = bot.get_channel(CHANNEL_ID)
    await check_agslist(channel)

@bot.event
async def on_ready():
    print(Fore.GREEN + f'Bot is online as {bot.user}' + Style.RESET_ALL)
    await bot.tree.sync()
    print(Fore.GREEN + "The bot is ready and commands have been synchronized." + Style.RESET_ALL)
    channel = bot.get_channel(CHANNEL_ID)
    await check_agslist(channel)
    auto_update_agslist.start()

@bot.command(name='updateallist')
async def update_agslist(ctx):
    await ctx.message.delete()
    await check_agslist(ctx.channel)

@tasks.loop(minutes=1)
async def countdown_timer():
    next_run_in = auto_update_agslist.next_iteration - discord.utils.utcnow()
    minutes, seconds = divmod(next_run_in.total_seconds(), 60)
    print(Fore.GREEN + f"Next update in {int(minutes)} minutes and {int(seconds)} seconds" + Style.RESET_ALL)

async def main():
    settings = load_settings()
    bot.settings = settings
    await bot.load_extension("cogs.w")
    await bot.load_extension("cogs.gift")
    await bot.load_extension("cogs.addadmin")
    await bot.load_extension("cogs.allist")
    await bot.load_extension("cogs.list")
    await bot.load_extension("cogs.nf")
    await bot.load_extension("cogs.gncommand")
    

    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
