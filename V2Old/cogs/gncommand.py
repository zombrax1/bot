import discord
from discord.ext import commands
from discord import app_commands

class GNCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn 
        self.c = self.conn.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.c.execute("SELECT id FROM admin LIMIT 1")
            result = self.c.fetchone()
            
            if result:
                admin_id = result[0]
                admin_user = await self.bot.fetch_user(admin_id)
                
                if admin_user:
                    embed = discord.Embed(
                        title="Bot Active",
                        description="The bot has been successfully activated.",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="Developer Contact",
                        value="Developer: <@918825495456514088>\n"
                              "Discord Link: [dc.gg/whiteoutall](https://dc.gg/whiteoutall)",
                        inline=False
                    )
                    await admin_user.send(embed=embed)
                    print("Activation message sent to the admin user.")
                else:
                    print(f"User with Admin ID {admin_id} not found.")
            else:
                print("No record found in the admin table.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @app_commands.command(name="channel", description="Learn the ID of a channel.")
    @app_commands.describe(channel="The channel you want to learn the ID of")
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message(
            f"The ID of the selected channel is: {channel.id}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(GNCommands(bot))
