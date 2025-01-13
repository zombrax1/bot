import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

    @app_commands.command(name="addadmin", description="Adds an admin by Discord ID. Can only be used by the initial admin.")
    async def addadmin(self, interaction: discord.Interaction, member: discord.Member):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY)''')
        self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM admin")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            if interaction.user.id != member.id:
                await interaction.response.send_message(
                    "This is the first admin being added. Please use the command only for yourself; "
                    "adding someone else is not allowed.",
                    ephemeral=True
                )
                return
            cursor.execute("INSERT INTO admin (id) VALUES (?)", (member.id,))
            self.conn.commit()
            await interaction.response.send_message(f"{member.mention} has been successfully added as an admin.", ephemeral=True)
        else:
            cursor.execute("SELECT id FROM admin WHERE id = ?", (interaction.user.id,))
            is_authorized = cursor.fetchone()
            if not is_authorized:
                await interaction.response.send_message("Only current admins can use this command.", ephemeral=True)
                return

            cursor.execute("SELECT id FROM admin WHERE id = ?", (member.id,))
            if cursor.fetchone():
                await interaction.response.send_message(f"{member.mention} is already added as an admin.", ephemeral=True)
            else:
                cursor.execute("INSERT INTO admin (id) VALUES (?)", (member.id,))
                self.conn.commit()
                await interaction.response.send_message(f"{member.mention} has been successfully added as an admin.", ephemeral=True)

    @app_commands.command(name="listadmins", description="Lists all admins.")
    async def listadmins(self, interaction: discord.Interaction):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM admin")
        admin_list = cursor.fetchall()

        if admin_list:
            admin_mentions = [f"<@{admin_id[0]}>" for admin_id in admin_list]
            await interaction.response.send_message("Admins:\n" + "\n".join(admin_mentions), ephemeral=True)
        else:
            await interaction.response.send_message("No admin has been added.", ephemeral=True)

    @app_commands.command(name="removeadmin", description="Removes an admin by Discord ID. Only the initial admin can use this.")
    async def removeadmin(self, interaction: discord.Interaction, member: discord.Member):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id FROM admin ORDER BY id LIMIT 1")
        initial_admin = cursor.fetchone()
        
        if initial_admin and initial_admin[0] == interaction.user.id:
            cursor.execute("SELECT id FROM admin WHERE id = ?", (member.id,))
            if cursor.fetchone():
                cursor.execute("DELETE FROM admin WHERE id = ?", (member.id,))
                self.conn.commit()
                await interaction.response.send_message(f"{member.mention} has been successfully removed from the admin list.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{member.mention} is not in the admin list.", ephemeral=True)
        else:
            await interaction.response.send_message("Only the initially added admin can use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
