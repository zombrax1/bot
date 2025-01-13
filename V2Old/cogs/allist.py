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

        embed = discord.Embed(
            title="User Addition in Progress...",
            description="User addition process is ongoing...",
            color=discord.Color.blue()
        )
        embed.add_field(name="Successfully Added Users (0)", value="-", inline=False)
        embed.add_field(name="Users with Errors (0)", value="-", inline=False)
        embed.add_field(name="Already Existing Users (0)", value="-", inline=False)

        add_message = await interaction.channel.send(embed=embed)

        added_count = 0
        already_exists_count = 0
        error_count = 0

        added_users = []
        already_exists_users = []
        error_users = []

        id_list = ids.split(',')
        for fid in id_list:
            fid = fid.strip()
            if not fid:
                error_count += 1
                error_users.append(fid)
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
                                error_count += 1
                                error_users.append(fid)
                                break

                            nickname = data['data'][0]['nickname'] if isinstance(data['data'], list) and data['data'] else data['data'].get('nickname', None)
                            furnace_lv = data['data'][0].get('stove_lv', 0) if isinstance(data['data'], list) and data['data'] else data['data'].get('stove_lv', 0)

                            if nickname:
                                self.c.execute("SELECT * FROM users WHERE fid=?", (fid,))
                                result = self.c.fetchone()

                                if result is None:
                                    self.c.execute("INSERT INTO users (fid, nickname, furnace_lv) VALUES (?, ?, ?)", (fid, nickname, furnace_lv))
                                    self.conn.commit()
                                    added_count += 1
                                    added_users.append(nickname)
                                else:
                                    already_exists_count += 1
                                    already_exists_users.append(nickname)
                            else:
                                error_count += 1
                                error_users.append(fid)
                            break

                        elif response.status == 429:
                            await asyncio.sleep(60)
                            continue
                        else:
                            error_count += 1
                            error_users.append(fid)
                            break

            if added_count % 10 == 0:
                embed.set_field_at(0, name=f"Successfully Added Users ({added_count})", value=", ".join(added_users) or "-", inline=False)
                embed.set_field_at(1, name=f"Users with Errors ({error_count})", value=", ".join(error_users) or "-", inline=False)
                embed.set_field_at(2, name=f"Already Existing Users ({already_exists_count})", value=", ".join(already_exists_users) or "-", inline=False)
                embed.description = "User addition process is ongoing..."

                await add_message.edit(embed=embed)

        embed.set_field_at(0, name=f"Successfully Added Users ({added_count})", value=", ".join(added_users) or "-", inline=False)
        embed.set_field_at(1, name=f"Users with Errors ({error_count})", value=", ".join(error_users) or "-", inline=False)
        embed.set_field_at(2, name=f"Already Existing Users ({already_exists_count})", value=", ".join(already_exists_users) or "-", inline=False)
        embed.title = "User Addition Completed"
        embed.description = "User addition process completed."

        await add_message.edit(embed=embed)

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
