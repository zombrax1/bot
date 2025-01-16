import discord
from discord.ext import commands
import sqlite3

class OtherFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def show_other_features_menu(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="🔧 Other Features",
                description=(
                    "This section was created according to users' requests:\n\n"
                    "**Available Operations**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🐻 **Bear Trap**\n"
                    "└ Time notification system\n"
                    "└ Not just for Bear! Use it for any event:\n"
                    "   Bear - KE - Forst - CJ and everything else\n"
                    "└ Add unlimited notifications\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=discord.Color.blue()
            )
            
            view = OtherFeaturesView(self)
            
            try:
                await interaction.response.edit_message(embed=embed, view=view)
            except discord.InteractionResponded:
                pass
                
        except Exception as e:
            print(f"Error in show_other_features_menu: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )

class OtherFeaturesView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Bear Trap",
        emoji="🐻",
        style=discord.ButtonStyle.primary,
        custom_id="bear_trap",
        row=0
    )
    async def bear_trap_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            bear_trap_cog = self.cog.bot.get_cog("BearTrap")
            if bear_trap_cog:
                await bear_trap_cog.show_bear_trap_menu(interaction)
            else:
                await interaction.response.send_message(
                    "❌ Bear Trap module not found.",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Bear Trap menu: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while loading Bear Trap menu.",
                ephemeral=True
            )

    @discord.ui.button(
        label="Main Menu",
        emoji="🏠",
        style=discord.ButtonStyle.secondary,
        custom_id="main_menu",
        row=2
    )
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            alliance_cog = self.cog.bot.get_cog("Alliance")
            if alliance_cog:
                await alliance_cog.show_main_menu(interaction)
        except Exception as e:
            print(f"Error returning to main menu: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while returning to main menu.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(OtherFeatures(bot)) 
