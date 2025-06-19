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
        self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
        admin_record = self.settings_cursor.fetchone()
        if not admin_record or admin_record[0] != 1:
            await interaction.response.send_message("❌ Only global administrators can remove log channels.", ephemeral=True)
            return

        # Fetch alliances that have logs set up AND are in the target_guild
        query = """
            SELECT al.alliance_id, al_list.name, al.channel_id
            FROM alliance_logs al
            JOIN alliance_list al_list ON al.alliance_id = al_list.alliance_id
            WHERE al_list.discord_server_id = ?
        """
        self.settings_cursor.execute(query, (target_guild.id,))
        log_entries = self.settings_cursor.fetchall()

        if not log_entries:
            await interaction.response.send_message(f"❌ No alliance log channels found for alliances in **{target_guild.name}**.", ephemeral=True)
            return

        # Use discord.ui.Select for dynamic options based on log_entries
        options = []
        for alliance_id, alliance_name, channel_id in log_entries:
            channel = target_guild.get_channel(channel_id)
            channel_mention = f"<#{channel_id}>" if channel else f"ID: {channel_id} (channel not found)"
            options.append(discord.SelectOption(
                label=f"{alliance_name[:50]}",
                value=str(alliance_id),
                description=f"Logs to: {channel_mention[:45]}"
            ))

        if not options: # Should not happen if log_entries is not empty, but as a safeguard
             await interaction.response.send_message(f"❌ No valid log channel entries found for {target_guild.name}.", ephemeral=True)
             return

        select_menu = discord.ui.Select(placeholder="Select alliance to remove log channel for...", options=options)

        async def remove_log_select_callback(select_interaction: discord.Interaction):
            selected_alliance_id = int(select_menu.values[0])

            # Find the selected entry to display its details
            selected_entry = next((le for le in log_entries if le[0] == selected_alliance_id), None)
            if not selected_entry:
                await select_interaction.response.send_message("Error: Could not find selected alliance log entry.", ephemeral=True)
                return

            _, sel_alliance_name, sel_channel_id = selected_entry
            sel_channel = target_guild.get_channel(sel_channel_id)
            sel_channel_mention = f"<#{sel_channel_id}>" if sel_channel else f"ID: {sel_channel_id}"

            confirm_embed = discord.Embed(
                title="⚠️ Confirm Removal",
                description=(
                    f"Are you sure you want to remove the log channel for:\n\n"
                    f"🏰 **Alliance:** {sel_alliance_name}\n"
                    f"📝 **Current Log Channel:** {sel_channel_mention}\n\n"
                    "This action cannot be undone!"
                ),
                color=discord.Color.yellow()
            )

            confirm_view = discord.ui.View(timeout=60)

            async def confirm_action_callback(button_interaction: discord.Interaction):
                custom_id = button_interaction.data.get("custom_id")
                if custom_id == "confirm_remove_log":
                    self.settings_cursor.execute("DELETE FROM alliance_logs WHERE alliance_id = ?", (selected_alliance_id,))
                    self.settings_db.commit()
                    success_embed = discord.Embed(
                        title="✅ Log Channel Removed",
                        description=f"Log channel for **{sel_alliance_name}** (was <#{sel_channel_id}>) removed.",
                        color=discord.Color.green()
                    )
                    await button_interaction.response.edit_message(embed=success_embed, view=None)
                elif custom_id == "cancel_remove_log":
                    cancel_embed = discord.Embed(title="❌ Removal Cancelled", description="Log channel removal cancelled.", color=discord.Color.red())
                    await button_interaction.response.edit_message(embed=cancel_embed, view=None)

            confirm_btn = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_remove_log")
            cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_remove_log")
            confirm_btn.callback = confirm_action_callback
            cancel_btn.callback = confirm_action_callback
            confirm_view.add_item(confirm_btn)
            confirm_view.add_item(cancel_btn)

            await select_interaction.response.edit_message(embed=confirm_embed, view=confirm_view)

        select_menu.callback = remove_log_select_callback

        view = discord.ui.View(timeout=180)
        view.add_item(select_menu)

        initial_embed = discord.Embed(
            title="🗑️ Remove Log Channel",
            description=f"Select an alliance in **{target_guild.name}** to remove its log channel assignment.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=initial_embed, view=view, ephemeral=True)


    async def view_log_channels_handler(self, interaction: discord.Interaction, target_guild: discord.Guild):
        self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
        admin_record = self.settings_cursor.fetchone()
        if not admin_record or admin_record[0] != 1:
            await interaction.response.send_message("❌ Only global administrators can view log channels.", ephemeral=True)
            return

        query = """
            SELECT al_list.name, al.channel_id
            FROM alliance_logs al
            JOIN alliance_list al_list ON al.alliance_id = al_list.alliance_id
            WHERE al_list.discord_server_id = ?
            ORDER BY al_list.name
        """
        self.settings_cursor.execute(query, (target_guild.id,))
        log_entries = self.settings_cursor.fetchall()

        if not log_entries:
            await interaction.response.send_message(f"❌ No alliance log channels found for alliances in **{target_guild.name}**.", ephemeral=True)
            return

        list_embed = discord.Embed(
            title=f"📊 Alliance Log Channels for {target_guild.name}",
            description="Current log channel assignments for alliances in this server:\n\n",
            color=discord.Color.blue()
        )

        for alliance_name, channel_id in log_entries:
            channel = target_guild.get_channel(channel_id)
            channel_mention = f"<#{channel_id}> ({channel.name})" if channel else f"ID: {channel_id} (Channel not found or inaccessible)"
            list_embed.add_field(
                name=f"🏰 {alliance_name}",
                value=f"📝 **Log Channel:** {channel_mention}\n━━━━━━━━━━━━━━━━━━━━━━",
                inline=False
            )

        if not list_embed.fields: # Should be caught by "if not log_entries" but as an extra check
            list_embed.description = f"No log channels are currently set for alliances in **{target_guild.name}**."

        await interaction.response.send_message(embed=list_embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(LogSystem(bot))
