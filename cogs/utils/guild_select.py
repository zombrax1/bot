import discord
import sqlite3
from typing import List, Optional, Tuple

# Using a simple class instead of Pydantic for now to avoid adding dependencies
# if not already present. If Pydantic is used elsewhere, this can be converted.
class UserGuildInfo:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class GuildSelectView(discord.ui.View):
    def __init__(self, user_guilds: List[UserGuildInfo], placeholder: str = "Select a server"):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.selected_guild_id: Optional[int] = None
        self.interaction_to_follow_up: Optional[discord.Interaction] = None

        options = [
            discord.SelectOption(label=guild.name, value=str(guild.id), emoji="🏰")
            for guild in user_guilds
        ]

        self.select_menu = discord.ui.Select(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_guild_id = int(self.select_menu.values[0])
        self.interaction_to_follow_up = interaction # Store interaction for followup
        # No deferring here, let the calling function handle response.
        self.stop() # Stop the view once selection is made

async def get_admin_guilds(bot: discord.Client, admin_user_id: int) -> List[UserGuildInfo]:
    """
    Fetches the list of guilds an admin user is authorized to manage.
    """
    guilds_info: List[UserGuildInfo] = []

    # Database connections should ideally be managed by the cog calling this utility,
    # or passed as arguments. For simplicity here, opening new connections.
    # This is not ideal for performance if called very frequently.
    settings_conn = sqlite3.connect('db/settings.sqlite')
    settings_cursor = settings_conn.cursor()

    alliance_conn = sqlite3.connect('db/alliance.sqlite')
    alliance_cursor = alliance_conn.cursor()

    settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (admin_user_id,))
    admin_record = settings_cursor.fetchone()

    if not admin_record:
        settings_conn.close()
        alliance_conn.close()
        return guilds_info # Not an admin or not in admin table

    is_global_admin = admin_record[0] == 1

    if is_global_admin:
        # Global admin can manage all guilds the bot is in
        for guild in bot.guilds:
            guilds_info.append(UserGuildInfo(id=guild.id, name=guild.name))
    else:
        # General admin: fetch guilds from adminserver table
        settings_cursor.execute("SELECT DISTINCT alliances_id FROM adminserver WHERE admin = ?", (admin_user_id,))
        assigned_alliance_ids_tuples = settings_cursor.fetchall()

        if assigned_alliance_ids_tuples:
            assigned_alliance_ids = [item[0] for item in assigned_alliance_ids_tuples]

            # Fetch guild_id from alliance_list for these alliances
            # Assuming alliance_list has discord_server_id which is the guild_id
            # This part of the schema was noted in cogs/alliance.py
            placeholders = ','.join('?' for _ in assigned_alliance_ids)
            alliance_cursor.execute(f"SELECT DISTINCT discord_server_id FROM alliance_list WHERE alliance_id IN ({placeholders})", assigned_alliance_ids)
            guild_id_tuples = alliance_cursor.fetchall()

            for guild_id_tuple in guild_id_tuples:
                guild_id = guild_id_tuple[0]
                if guild_id: # Ensure discord_server_id is not NULL
                    guild = bot.get_guild(guild_id)
                    if guild:
                        # Avoid duplicates if an admin is tied to multiple alliances in the same server
                        if not any(g.id == guild.id for g in guilds_info):
                            guilds_info.append(UserGuildInfo(id=guild.id, name=guild.name))

    settings_conn.close()
    alliance_conn.close()
    return guilds_info

async def prompt_guild_selection(interaction: discord.Interaction, bot: discord.Client, admin_user_id: int, original_command_name: str = "settings") -> Optional[discord.Guild]:
    """
    Prompts an admin to select a guild if the interaction is in a DM and they manage multiple.
    Returns the selected discord.Guild object, or interaction.guild if already in a guild context.
    Returns None if selection is cancelled or no suitable guild is found.
    """
    if interaction.guild:
        # Already in a guild context, no selection needed.
        return interaction.guild

    # In DMs, fetch manageable guilds
    manageable_guilds_info = await get_admin_guilds(bot, admin_user_id)

    if not manageable_guilds_info:
        try:
            await interaction.response.send_message("You are not registered as an admin for any servers, or I couldn't find any servers you manage.", ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send("You are not registered as an admin for any servers, or I couldn't find any servers you manage.", ephemeral=True)
        return None

    if len(manageable_guilds_info) == 1:
        # Only one guild, no selection needed, just return it
        selected_guild = bot.get_guild(manageable_guilds_info[0].id)
        if not selected_guild:
             try:
                await interaction.response.send_message(f"I could not find the server '{manageable_guilds_info[0].name}' (ID: {manageable_guilds_info[0].id}) that you manage. It might have been removed or I might have left it.", ephemeral=True)
             except discord.errors.InteractionResponded:
                await interaction.followup.send(f"I could not find the server '{manageable_guilds_info[0].name}' (ID: {manageable_guilds_info[0].id}) that you manage. It might have been removed or I might have left it.", ephemeral=True)
        return selected_guild

    # Multiple guilds, prompt for selection
    view = GuildSelectView(manageable_guilds_info, placeholder=f"Select a server for /{original_command_name}")

    if interaction.response.is_done():
        # If initial response was deferred or already sent (e.g. from a modal submit)
        msg = await interaction.followup.send(
            f"You are using `/{original_command_name}` via DM. Please select which server you'd like to manage:",
            view=view,
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"You are using `/{original_command_name}` via DM. Please select which server you'd like to manage:",
            view=view,
            ephemeral=True
        )
        msg = await interaction.original_response() # Get the message object

    await view.wait() # Wait for the user to make a selection or timeout

    if view.selected_guild_id:
        selected_guild = bot.get_guild(view.selected_guild_id)
        if view.interaction_to_follow_up:
            # Clean up the selection message by removing the view
            try:
                await view.interaction_to_follow_up.edit_original_response(content=f"You selected: **{selected_guild.name if selected_guild else 'Unknown Server'}**.", view=None)
            except discord.HTTPException:
                 # This can happen if the interaction token expires or message is deleted.
                pass
        elif msg: # Fallback if interaction_to_follow_up was not set (should not happen with current view logic)
            try:
                await msg.edit(content=f"You selected: **{selected_guild.name if selected_guild else 'Unknown Server'}**.", view=None)
            except discord.HTTPException:
                pass
        return selected_guild
    else: # Timeout or no selection
        if view.interaction_to_follow_up:
            try:
                await view.interaction_to_follow_up.edit_original_response(content="Server selection timed out or was cancelled.", view=None)
            except discord.HTTPException:
                pass
        elif msg:
             try:
                await msg.edit(content="Server selection timed out or was cancelled.", view=None)
             except discord.HTTPException:
                pass
        return None
