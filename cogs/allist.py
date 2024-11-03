import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import hashlib
import ssl
import time

class Allist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret = bot.SECRET
        self.conn = bot.conn
        self.c = self.conn.cursor()

    async def is_admin(self, user_id: int) -> bool:
        self.c.execute("SELECT 1 FROM admin WHERE id=?", (user_id,))
        return self.c.fetchone() is not None

    async def fid_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            self.c.execute("SELECT fid, nickname FROM users")
            users = self.c.fetchall()

            choices = [
                discord.app_commands.Choice(name=f"{nickname} ({fid})", value=str(fid)) 
                for fid, nickname in users
            ]

            if current:
                filtered_choices = [choice for choice in choices if current.lower() in choice.name.lower()][:25]
            else:
                filtered_choices = choices[:25]

            return filtered_choices

        except Exception as e:
            print(f"Autocomplete failed to load: {e}")
            return []

    @app_commands.command(name="allistadd", description="Add users by IDs (comma-separated for multiple users)")
    async def add_user(self, interaction: discord.Interaction, ids: str):
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        added = []
        already_exists = []

        id_list = ids.split(',')
        for fid in id_list:
            fid = fid.strip()
            if not fid:
                already_exists.append(f"{fid} - Empty ID provided")
                continue

            current_time = int(time.time() * 1000)
            form = f"fid={fid}&time={current_time}"
            sign = hashlib.md5((form + self.secret).encode('utf-8')).hexdigest()
            form = f"sign={sign}&{form}"

            url = 'https://wos-giftcode-api.centurygame.com/api/player'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession() as session:
                while True:
                    async with session.post(url, headers=headers, data=form, ssl=ssl_context) as response:
                        if response.status == 200:
                            data = await response.json()

                            if not data['data']:
                                already_exists.append(f"{fid} - No data found")
                                break 

                            nickname = data['data'][0]['nickname'] if isinstance(data['data'], list) and data['data'] else data['data'].get('nickname', None)
                            furnace_lv = data['data'][0].get('stove_lv', 0) if isinstance(data['data'], list) and data['data'] else data['data'].get('stove_lv', 0)

                            if nickname:
                                self.c.execute("SELECT * FROM users WHERE fid=?", (fid,))
                                result = self.c.fetchone()

                                if result is None:
                                    self.c.execute("INSERT INTO users (fid, nickname, furnace_lv) VALUES (?, ?, ?)", (fid, nickname, furnace_lv))
                                    self.conn.commit()
                                    added.append({'fid': fid, 'nickname': nickname, 'furnace_lv': furnace_lv})
                                    print(f"Added: {fid} - {nickname}") 
                                else:
                                    already_exists.append(f"{fid} - Already exists")
                            else:
                                already_exists.append(f"{fid} - Nickname not found")
                            break 

                        elif response.status == 429:
                            print(f"Rate limit reached for {fid}. Waiting 1 minute...") 
                            await asyncio.sleep(60) 
                            continue 

                        else:
                            already_exists.append(f"{fid} - Request failed with status: {response.status}")
                            break  

        if added:
            embed = discord.Embed(
                title="Added People",
                description="The following users were successfully added:",
                color=discord.Color.green()
            )

            for user in added:
                embed.add_field(
                    name=user['nickname'],
                    value=f"Furnace Level: {user['furnace_lv']}\nID: {user['fid']}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        if already_exists:
            embed = discord.Embed(
                title="Already Exists / No Data Found",
                description="\n".join(already_exists),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="allistremove", description="Remove users by IDs (comma-separated for multiple users)")
    @app_commands.autocomplete(ids=fid_autocomplete)
    async def remove_user(self, interaction: discord.Interaction, ids: str):
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        removed_ids = []
        not_found_ids = []

        id_list = ids.split(',')
        for fid in id_list:
            fid = fid.strip()
            self.c.execute("SELECT * FROM users WHERE fid=?", (fid,))
            result = self.c.fetchone()
            
            if result:
                self.c.execute("DELETE FROM users WHERE fid=?", (fid,))
                self.conn.commit()
                removed_ids.append(fid)
            else:
                not_found_ids.append(fid)

        if removed_ids:
            await interaction.response.send_message(
                f"Removed users with IDs: {', '.join(removed_ids)}"
            )
        
        if not_found_ids:
            await interaction.followup.send(
                f"IDs not found in the list: {', '.join(not_found_ids)}"
            )

async def setup(bot):
    await bot.add_cog(Allist(bot))
