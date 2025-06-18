import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
from typing import Optional # Added
import discord # Added

from .alliance_member_operations import AllianceSelectView # May need adjustment if AllianceSelectView also needs guild_id
from .alliance import PaginatedChannelView # May need adjustment
from .utils.guild_select import prompt_guild_selection # Added

class LogSystemMenuView(discord.ui.View):
    def __init__(self, cog, target_guild_id: Optional[int], timeout=180):
        super().__init__(timeout=timeout)
        self.cog = cog # Instance of LogSystem cog
        self.target_guild_id = target_guild_id
        self.target_guild: Optional[discord.Guild] = None # Will be set in show_log_system_main_menu

        if self.target_guild_id:
            self.target_guild = self.cog.bot.get_guild(self.target_guild_id)

        # Define buttons
        self.add_item(discord.ui.Button(label="Set Log Channel", emoji="📝", style=discord.ButtonStyle.primary, custom_id="logsys_set_channel", row=0))
        self.add_item(discord.ui.Button(label="Remove Log Channel", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="logsys_remove_channel", row=0))
        self.add_item(discord.ui.Button(label="View Log Channel", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="logsys_view_channel", row=1))
        # Main Menu button will navigate back to Bot Operations, passing target_guild_id
        self.add_item(discord.ui.Button(label="Main Menu", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="logsys_main_menu", row=2))

    @discord.ui.button(label="Set Log Channel", emoji="📝", style=discord.ButtonStyle.primary, custom_id="logsys_set_channel", row=0)
    async def set_log_channel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.target_guild: # Should be set by show_log_system_main_menu
            await interaction.response.send_message("Guild context not available.", ephemeral=True)
            return
        await self.cog.set_log_channel_handler(interaction, self.target_guild)

    @discord.ui.button(label="Remove Log Channel", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="logsys_remove_channel", row=0)
    async def remove_log_channel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.target_guild:
            await interaction.response.send_message("Guild context not available.", ephemeral=True)
            return
        await self.cog.remove_log_channel_handler(interaction, self.target_guild)

    @discord.ui.button(label="View Log Channel", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="logsys_view_channel", row=1)
    async def view_log_channel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.target_guild:
            await interaction.response.send_message("Guild context not available.", ephemeral=True)
            return
        await self.cog.view_log_channel_handler(interaction, self.target_guild)

    @discord.ui.button(label="Main Menu", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="logsys_main_menu", row=2)
    async def main_menu_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Navigate back to Bot Operations menu
        bot_ops_cog = self.cog.bot.get_cog("BotOperations")
        if bot_ops_cog and hasattr(bot_ops_cog, 'show_bot_operations_menu'):
            # Pass target_guild (which is already a Guild object here)
            await bot_ops_cog.show_bot_operations_menu(interaction, self.target_guild)
        else:
            await interaction.response.edit_message(content="Bot Operations module not found or is outdated.", view=None, embed=None)


class LogSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_db = sqlite3.connect('db/settings.sqlite', check_same_thread=False)
        self.settings_cursor = self.settings_db.cursor()
        
        self.alliance_db = sqlite3.connect('db/alliance.sqlite', check_same_thread=False)
        self.alliance_cursor = self.alliance_db.cursor()
        
        self.setup_database()

    def setup_database(self):
        try:
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS alliance_logs (
                    alliance_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    FOREIGN KEY (alliance_id) REFERENCES alliance_list (alliance_id)
                )
            """)
            
            self.settings_db.commit()
                
        except Exception as e:
            print(f"Error setting up log system database: {e}")

    def __del__(self):
        try:
            self.settings_db.close()
            self.alliance_db.close()
        except:
            pass

    # @commands.Cog.listener() # Comment out or remove if no other component interactions handled here
    # async def on_interaction(self, interaction: discord.Interaction):
    #     # Logic for custom_ids like "set_log_channel", "remove_log_channel", "view_log_channels"
    #     # will be handled by the LogSystemMenuView callbacks now.
    #     # The main entry "log_system" custom_id (from BotOperationsView) will call show_log_system_main_menu.
    #     pass

    async def show_log_system_main_menu(self, interaction: discord.Interaction, target_guild: Optional[discord.Guild]):
        user_id = interaction.user.id
        self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (user_id,))
        admin_record = self.settings_cursor.fetchone()

        if not admin_record or admin_record[0] != 1: # Assuming only global admins manage log system
            await interaction.response.send_message(
                "❌ Only global administrators can access the log system.",
                ephemeral=True
            )
            return

        # If target_guild is None, it means this might have been called from a context
        # where guild selection is needed (e.g., DM if this was a slash command, or if BotOperationsView didn't pass it).
        # For LogSystem, operations are often guild-specific (setting a log channel *for an alliance in a guild*).
        # However, the original on_interaction for "log_system" custom_id didn't seem to use guild context for the main menu.
        # The sub-operations (set, remove, view) did.
        # Let's assume for now the main menu itself doesn't strictly need a pre-selected target_guild,
        # but the handlers it calls will. The view will pass its stored target_guild_id.
        
        # If this menu is intended to operate on a specific guild context immediately,
        # and target_guild is None, we might need to prompt.
        # For this refactor, the prompt_guild_selection is not strictly added here yet,
        # as the main menu display itself doesn't use it.
        # The buttons in the view will pass the target_guild_id they were initialized with.

        # If target_guild is passed, we use its ID for the view.
        current_target_guild_id = target_guild.id if target_guild else None

        log_embed = discord.Embed(
            title="📋 Alliance Log System",
            description=(
                "Select an option to manage alliance logs:\n\n"
                "**Available Options**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📝 **Set Log Channel**\n"
                "└ Assign a log channel to an alliance\n\n"
                "🗑️ **Remove Log Channel**\n"
                "└ Remove alliance log channel\n\n"
                "📊 **View Log Channels**\n"
                "└ List all alliance log channels\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.blue()
        )

        view = LogSystemMenuView(self, target_guild_id=current_target_guild_id)
        view.target_guild = target_guild # Set the guild object on the view instance for callbacks

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=log_embed, view=view)
        else:
            # This path might be taken if show_log_system_main_menu is called directly by a command
            # For now, assume it's called from BotOperationsView button, so edit_message is typical
            await interaction.response.edit_message(embed=log_embed, view=view)


    async def set_log_channel_handler(self, interaction: discord.Interaction, target_guild: discord.Guild):
        # Placeholder: Implement actual logic for setting log channel
        # This will involve selecting an alliance (perhaps filtered by target_guild if not global admin)
        # and then selecting a channel from target_guild.text_channels.
        # Original logic from on_interaction for "set_log_channel" needs to be adapted here.

        # Quick check for global admin for this specific operation
        self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
        admin_record = self.settings_cursor.fetchone()
        if not admin_record or admin_record[0] != 1:
            await interaction.response.send_message("❌ Only global administrators can set log channels.", ephemeral=True)
            return

        # --- Start of adapted logic from original "set_log_channel" ---
        self.alliance_cursor.execute("SELECT alliance_id, name FROM alliance_list ORDER BY name")
        alliances = self.alliance_cursor.fetchall()

        if not alliances:
            await interaction.response.send_message("❌ No alliances found.", ephemeral=True)
            return

        alliances_with_counts = []
        # This part might need adjustment if users DB connection isn't readily available or efficient to open per call
        for alliance_id, name in alliances:
            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                member_count = cursor.fetchone()[0]
                alliances_with_counts.append((alliance_id, name, member_count))

        alliance_embed = discord.Embed(
            title="📝 Set Log Channel - Select Alliance",
            description="Please select an alliance:", color=discord.Color.blue()
        )
        # AllianceSelectView might need target_guild for filtering if not global admin
        # For global admin setting logs, they see all alliances.
        alliance_select_view = AllianceSelectView(alliances_with_counts, self)

        async def set_log_alliance_select_callback(select_interaction: discord.Interaction): # Renamed
            selected_alliance_id = int(alliance_select_view.current_select.values[0])

            channel_embed = discord.Embed(
                title="📝 Set Log Channel - Select Channel",
                description=f"Please select a channel in **{target_guild.name}** for logging alliance activities.",
                color=discord.Color.blue()
            )

            async def set_log_channel_select_callback(channel_interaction: discord.Interaction): # Renamed
                selected_channel_id = int(channel_interaction.data["values"][0])
                
                self.settings_cursor.execute(
                    "INSERT OR REPLACE INTO alliance_logs (alliance_id, channel_id) VALUES (?, ?)",
                    (selected_alliance_id, selected_channel_id)
                )
                self.settings_db.commit()

                self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (selected_alliance_id,))
                alliance_name_val = self.alliance_cursor.fetchone()[0] # Renamed

                success_embed = discord.Embed(
                    title="✅ Log Channel Set",
                    description=(
                        f"Successfully set log channel for **{alliance_name_val}** to <#{selected_channel_id}> "
                        f"in server **{target_guild.name}**."
                    ),
                    color=discord.Color.green()
                )
                await channel_interaction.response.edit_message(embed=success_embed, view=None)

            # Use target_guild passed to the handler
            guild_channels = target_guild.text_channels
            if not guild_channels:
                await select_interaction.response.send_message(f"No text channels found in {target_guild.name}.",ephemeral=True)
                return

            channel_paginated_view = PaginatedChannelView(guild_channels, set_log_channel_select_callback) # Renamed
            await select_interaction.response.edit_message(embed=channel_embed, view=channel_paginated_view)

        alliance_select_view.callback = set_log_alliance_select_callback
        # The initial response for "Set Log Channel" button press
        await interaction.response.send_message(embed=alliance_embed, view=alliance_select_view, ephemeral=True)
        # --- End of adapted logic ---


    async def remove_log_channel_handler(self, interaction: discord.Interaction, target_guild: discord.Guild):
        # Placeholder: Implement actual logic for removing log channel
        # Needs to list alliances with set log channels (perhaps filtered by target_guild)
        # and then confirm removal. Original logic from "remove_log_channel" needs adaptation.
        await interaction.response.send_message(f"Placeholder for removing log channel for guild: {target_guild.name if target_guild else 'N/A'}. This feature is under development.", ephemeral=True)

    async def view_log_channel_handler(self, interaction: discord.Interaction, target_guild: discord.Guild):
        # Placeholder: Implement actual logic for viewing log channels
        # This should list alliances and their assigned log channels, possibly filtered by target_guild.
        # Original logic from "view_log_channels" needs adaptation.
        await interaction.response.send_message(f"Placeholder for viewing log channels for guild: {target_guild.name if target_guild else 'N/A'}. This feature is under development.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(LogSystem(bot))
