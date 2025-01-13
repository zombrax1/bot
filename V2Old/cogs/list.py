import discord
from discord.ext import commands
from discord import app_commands
from rich.table import Table
from rich.console import Console

def fix_rtl(text):
    return f"\u202B{text}\u202C"

class List(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret = bot.SECRET
        self.ALLIANCE_NAME = bot.ALLIANCE_NAME
        self.conn = bot.conn
        self.c = self.conn.cursor()

        self.level_mapping = {
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

    @app_commands.command(name='allist')
    async def show_users(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            self.c.execute("SELECT * FROM users ORDER BY furnace_lv DESC")
            users = self.c.fetchall()
            user_count = len(users)

            embed_title = f"{self.ALLIANCE_NAME} ALLIANCE LIST ({user_count} members)"
            table = Table(title=embed_title)
            table.add_column("Name", justify="center")
            table.add_column("FL", justify="center")
            table.add_column("Game ID", justify="center")

            for user in users:
                fid, nickname, furnace_lv = user
                
                level_display = self.level_mapping.get(furnace_lv, str(furnace_lv))
                formatted_nickname = fix_rtl(nickname) if any("\u0600" <= c <= "\u06FF" for c in nickname) else nickname
                
                table.add_row(formatted_nickname, level_display, str(fid))

            console = Console(record=True)
            console.print(table)
            output = console.export_text()

            lines = output.splitlines()
            max_length = 4000
            parts = []
            current_part = ""

            for line in lines:
                if len(current_part) + len(line) + 1 > max_length:
                    parts.append(current_part)
                    current_part = line + "\n"
                else:
                    current_part += line + "\n"

            if current_part:
                parts.append(current_part)

            for idx, part in enumerate(parts):
                if idx == 0:
                    embed = discord.Embed(title=embed_title, description=f"```\n{part}\n```", color=discord.Color.green())
                else:
                    embed = discord.Embed(description=f"```\n{part}\n```", color=discord.Color.green())
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(List(bot))
