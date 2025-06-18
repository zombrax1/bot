import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import os
import sqlite3
import asyncio
import requests
from .alliance_member_operations import AllianceSelectView


# Ensure typing.Optional and discord are imported (already done by previous Optional import)

class BotOperationsView(discord.ui.View):
    def __init__(self, cog, target_guild_id: Optional[int], timeout=180):
        super().__init__(timeout=timeout)
        self.cog = cog # Instance of BotOperations cog
        self.target_guild_id = target_guild_id

        # Define buttons. Callbacks will use placeholder logic for now.
        # Row 1
        self.add_item(discord.ui.Button(label="Add Admin", emoji="➕", style=discord.ButtonStyle.success, custom_id="bot_cmd_add_admin", row=1))
        self.add_item(discord.ui.Button(label="Remove Admin", emoji="➖", style=discord.ButtonStyle.danger, custom_id="bot_cmd_remove_admin", row=1))
        self.add_item(discord.ui.Button(label="View Administrators", emoji="👥", style=discord.ButtonStyle.primary, custom_id="bot_cmd_view_admins", row=1))
        # Row 2
        self.add_item(discord.ui.Button(label="Assign Alliance to Admin", emoji="🔗", style=discord.ButtonStyle.success, custom_id="bot_cmd_assign_alliance", row=2))
        self.add_item(discord.ui.Button(label="Delete Admin Permissions", emoji="➖", style=discord.ButtonStyle.danger, custom_id="bot_cmd_view_admin_perms", row=2))
        # Row 3
        self.add_item(discord.ui.Button(label="Transfer Old Database", emoji="🔄", style=discord.ButtonStyle.primary, custom_id="bot_cmd_transfer_db", row=3))
        self.add_item(discord.ui.Button(label="Check for Updates", emoji="🔄", style=discord.ButtonStyle.primary, custom_id="bot_cmd_check_updates", row=3))
        self.add_item(discord.ui.Button(label="Log System", emoji="📋", style=discord.ButtonStyle.primary, custom_id="bot_cmd_log_system_entry", row=3))
        self.add_item(discord.ui.Button(label="Alliance Control Messages", emoji="💬", style=discord.ButtonStyle.primary, custom_id="bot_cmd_alliance_control_msg", row=3))
        # Row 4
        self.add_item(discord.ui.Button(label="Main Menu", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="bot_cmd_main_menu", row=4))

    # Add placeholder callbacks for each button using @discord.ui.button if preferred,
    # or rely on the cog's on_interaction to handle these custom_ids for now.
    # For this subtask, we will rely on the cog's existing on_interaction to handle these.
    # So, no new @discord.ui.button methods needed in this View for this specific subtask.


class BotOperations(commands.Cog):
    def __init__(self, bot, conn):
        self.bot = bot
        self.conn = conn
        self.settings_db = sqlite3.connect('db/settings.sqlite', check_same_thread=False)
        self.settings_cursor = self.settings_db.cursor()
        self.alliance_db = sqlite3.connect('db/alliance.sqlite', check_same_thread=False)
        self.c_alliance = self.alliance_db.cursor()
        self.setup_database()

    async def add_admin_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()
            
            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command",
                    ephemeral=True
                )
                return

            # Using followup as the initial interaction (button press) should be deferred or responded to.
            # For simplicity, assuming the button press interaction was deferred or already had an initial response.
            await interaction.response.send_message( # Changed from followup to send_message for initial response from handler
                "Please tag the admin you want to add (@user).",
                ephemeral=True
            )

            def check(m):
                return m.author.id == interaction.user.id and m.channel == interaction.channel and len(m.mentions) == 1

            try:
                message = await self.bot.wait_for('message', timeout=30.0, check=check)
                new_admin = message.mentions[0]
                
                await message.delete()
                
                self.settings_cursor.execute("""
                    INSERT OR IGNORE INTO admin (id, is_initial)
                    VALUES (?, 0)
                """, (new_admin.id,))
                self.settings_db.commit()

                success_embed = discord.Embed(
                    title="✅ Administrator Successfully Added",
                    description=(
                        f"**New Administrator Information**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 **Name:** {new_admin.name}\n"
                        f"🆔 **Discord ID:** {new_admin.id}\n"
                        f"📅 **Account Creation Date:** {new_admin.created_at.strftime('%d/%m/%Y')}\n"
                    ),
                    color=discord.Color.green()
                )
                success_embed.set_thumbnail(url=new_admin.display_avatar.url)
                
                # Edit the original message that asked to tag a user
                await interaction.edit_original_response(
                    content=None,
                    embed=success_embed
                )

            except asyncio.TimeoutError:
                await interaction.edit_original_response(
                    content="❌ Timeout No user has been tagged.",
                    embed=None
                )

        except Exception as e:
            # Error handling for the handler itself
            if not interaction.response.is_done():
                 await interaction.response.send_message("Error in add_admin_handler.", ephemeral=True)
            else:
                 await interaction.followup.send("Error in add_admin_handler.", ephemeral=True)


    async def remove_admin_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()

            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command.",
                    ephemeral=True
                )
                return

            self.settings_cursor.execute("""
                SELECT id, is_initial FROM admin
                ORDER BY is_initial DESC, id
            """)
            admins = self.settings_cursor.fetchall()

            if not admins:
                await interaction.response.send_message(
                    "❌ No administrator registered in the system.",
                    ephemeral=True
                )
                return

            admin_select_embed = discord.Embed(
                title="👤 Administrator Deletion",
                description=(
                    "Select the administrator you want to delete:\n\n"
                    "**Administrator List**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                ),
                color=discord.Color.red()
            )

            options = []
            for admin_id, is_initial in admins:
                try:
                    user = await self.bot.fetch_user(admin_id)
                    admin_name = f"{user.name}"
                except:
                    admin_name = "Unknown User"

                options.append(
                    discord.SelectOption(
                        label=f"{admin_name[:50]}",
                        value=str(admin_id),
                        description=f"{'Global Admin' if is_initial == 1 else 'Server Admin'} - ID: {admin_id}",
                        emoji="👑" if is_initial == 1 else "👤"
                    )
                )

            admin_select = discord.ui.Select(
                placeholder="Select the administrator you want to delete...",
                options=options,
                custom_id="admin_select_for_removal" # Ensure unique custom_id if needed elsewhere
            )

            admin_view = discord.ui.View(timeout=None) # Consider timeout
            admin_view.add_item(admin_select)

            async def remove_admin_select_callback(select_interaction: discord.Interaction): # Renamed for clarity
                try:
                    selected_admin_id = int(select_interaction.data["values"][0])

                    self.settings_cursor.execute("""
                        SELECT id, is_initial FROM admin WHERE id = ?
                    """, (selected_admin_id,))
                    admin_info = self.settings_cursor.fetchone()

                    self.settings_cursor.execute("""
                        SELECT alliances_id
                        FROM adminserver
                        WHERE admin = ?
                    """, (selected_admin_id,))
                    admin_alliances = self.settings_cursor.fetchall()

                    alliance_names = []
                    if admin_alliances:
                        alliance_ids = [alliance[0] for alliance in admin_alliances]

                        alliance_cursor = self.alliance_db.cursor()
                        placeholders = ','.join('?' * len(alliance_ids))
                        query = f"SELECT alliance_id, name FROM alliance_list WHERE alliance_id IN ({placeholders})"
                        alliance_cursor.execute(query, alliance_ids)

                        alliance_results = alliance_cursor.fetchall()
                        alliance_names = [alliance[1] for alliance in alliance_results]

                    try:
                        user = await self.bot.fetch_user(selected_admin_id)
                        admin_name_display = user.name # Use a different variable name
                        avatar_url = user.display_avatar.url
                    except Exception as e:
                        admin_name_display = f"Bilinmeyen Kullanıcı ({selected_admin_id})"
                        avatar_url = None

                    info_embed = discord.Embed(
                        title="⚠️ Administrator Deletion Confirmation",
                        description=(
                            f"**Administrator Information**\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"👤 **Name:** `{admin_name_display}`\n"
                            f"🆔 **Discord ID:** `{selected_admin_id}`\n"
                            f"👤 **Access Level:** `{'Global Admin' if admin_info[1] == 1 else 'Server Admin'}`\n"
                            f"🔍 **Access Type:** `{'All Alliances' if admin_info[1] == 1 else 'Server + Special Access'}`\n"
                            f"📊 **Available Alliances:** `{len(alliance_names)}`\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                        ),
                        color=discord.Color.yellow()
                    )

                    if alliance_names:
                        info_embed.add_field(
                            name="🏰 Alliances Authorized",
                            value="\n".join([f"• {name}" for name in alliance_names[:10]]) +
                                  ("\n• ..." if len(alliance_names) > 10 else ""),
                            inline=False
                        )
                    else:
                        info_embed.add_field(
                            name="🏰 Alliances Authorized",
                            value="This manager does not yet have an authorized alliance.",
                            inline=False
                        )

                    if avatar_url:
                        info_embed.set_thumbnail(url=avatar_url)

                    confirm_view_buttons = discord.ui.View(timeout=60) # Consider timeout

                    confirm_button = discord.ui.Button(
                        label="Confirm",
                        style=discord.ButtonStyle.danger,
                        custom_id="confirm_remove_admin_action" # Unique custom_id
                    )
                    cancel_button = discord.ui.Button(
                        label="Cancel",
                        style=discord.ButtonStyle.secondary,
                        custom_id="cancel_remove_admin_action" # Unique custom_id
                    )

                    async def confirm_remove_admin_button_callback(button_interaction: discord.Interaction): # Renamed
                        try:
                            self.settings_cursor.execute("DELETE FROM adminserver WHERE admin = ?", (selected_admin_id,))
                            self.settings_cursor.execute("DELETE FROM admin WHERE id = ?", (selected_admin_id,))
                            self.settings_db.commit()

                            success_embed = discord.Embed(
                                title="✅ Administrator Deleted Successfully",
                                description=(
                                    f"**Deleted Administrator**\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"👤 **Name:** `{admin_name_display}`\n"
                                    f"🆔 **Discord ID:** `{selected_admin_id}`\n"
                                ),
                                color=discord.Color.green()
                            )
                            
                            await button_interaction.response.edit_message(
                                embed=success_embed,
                                view=None
                            )
                        except Exception as e:
                            await button_interaction.response.send_message(
                                "❌ An error occurred while deleting the administrator.",
                                ephemeral=True
                            )

                    async def cancel_remove_admin_button_callback(button_interaction: discord.Interaction): # Renamed
                        cancel_embed = discord.Embed(
                            title="❌ Process Canceled",
                            description="Administrator deletion canceled.",
                            color=discord.Color.red()
                        )
                        await button_interaction.response.edit_message(
                            embed=cancel_embed,
                            view=None
                        )

                    confirm_button.callback = confirm_remove_admin_button_callback
                    cancel_button.callback = cancel_remove_admin_button_callback

                    confirm_view_buttons.add_item(confirm_button)
                    confirm_view_buttons.add_item(cancel_button)

                    await select_interaction.response.edit_message( # Edit the message with the select
                        embed=info_embed,
                        view=confirm_view_buttons
                    )

                except Exception as e:
                    await select_interaction.response.send_message(
                        "❌ An error occurred during processing.",
                        ephemeral=True
                    )

            admin_select.callback = remove_admin_select_callback

            await interaction.response.send_message( # Initial response for the handler
                embed=admin_select_embed,
                view=admin_view,
                ephemeral=True
            )

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error in remove_admin_handler.", ephemeral=True)
            else:
                await interaction.followup.send("Error in remove_admin_handler.", ephemeral=True)

    async def view_administrators_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()

            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command.",
                    ephemeral=True
                )
                return

            self.settings_cursor.execute("""
                SELECT a.id, a.is_initial
                FROM admin a
                ORDER BY a.is_initial DESC, a.id
            """)
            admins = self.settings_cursor.fetchall()

            if not admins:
                await interaction.response.send_message(
                    "❌ No administrators found in the system.",
                    ephemeral=True
                )
                return

            admin_list_embed = discord.Embed(
                title="👥 Administrator List",
                description="List of all administrators and their permissions:\n━━━━━━━━━━━━━━━━━━━━━━",
                color=discord.Color.blue()
            )

            for admin_id_tuple, is_initial_tuple in admins: # Unpack tuples
                admin_id = admin_id_tuple[0] if isinstance(admin_id_tuple, tuple) else admin_id_tuple
                is_initial = is_initial_tuple[0] if isinstance(is_initial_tuple, tuple) else is_initial_tuple
                try:
                    user = await self.bot.fetch_user(admin_id)
                    admin_name = user.name
                    # admin_avatar = user.display_avatar.url # Not used in original embed field

                    self.settings_cursor.execute("""
                        SELECT alliances_id
                        FROM adminserver
                        WHERE admin = ?
                    """, (admin_id,))
                    alliance_ids = self.settings_cursor.fetchall()

                    alliance_names = []
                    if alliance_ids:
                        alliance_id_list = [aid[0] for aid in alliance_ids]
                        placeholders = ','.join('?' * len(alliance_id_list))
                        self.c_alliance.execute(f"""
                            SELECT name
                            FROM alliance_list
                            WHERE alliance_id IN ({placeholders})
                        """, alliance_id_list)
                        alliance_names = [name[0] for name in self.c_alliance.fetchall()]

                    admin_info = (
                        f"👤 **Name:** {admin_name}\n"
                        f"🆔 **ID:** {admin_id}\n"
                        f"👑 **Role:** {'Global Admin' if is_initial == 1 else 'Server Admin'}\n"
                        f"🔍 **Access Type:** {'All Alliances' if is_initial == 1 else 'Server + Special Access'}\n"
                    )

                    if alliance_names:
                        alliance_text = "\n".join([f"• {name}" for name in alliance_names[:5]])
                        if len(alliance_names) > 5:
                            alliance_text += f"\n• ... and {len(alliance_names) - 5} more"
                        admin_info += f"🏰 **Managing Alliances:**\n{alliance_text}\n"
                    else:
                        admin_info += "🏰 **Managing Alliances:** No alliances assigned\n"

                    admin_list_embed.add_field(
                        name=f"{'👑' if is_initial == 1 else '👤'} {admin_name}",
                        value=f"{admin_info}\n━━━━━━━━━━━━━━━━━━━━━━",
                        inline=False
                    )

                except Exception as e:
                    admin_list_embed.add_field(
                        name=f"Unknown User ({admin_id})",
                        value="Error loading administrator information\n━━━━━━━━━━━━━━━━━━━━━━",
                        inline=False
                    )

            # The view for this handler might just be a "Back" button or nothing if it's just info.
            # For now, sending without a new view, as the original interaction's view (BotOperationsView) is still active.
            # If this message should replace the BotOperationsView, then a new view with a back button is needed.
            # The prompt asks to adapt interaction responses. This implies the original view might be replaced.
            # Let's assume for now it's a new message.
            await interaction.response.send_message( # Changed to send_message
                embed=admin_list_embed,
                ephemeral=True
                # view=view # If a new view with a back button is desired
            )

        except Exception as e:
            if not interaction.response.is_done():
                 await interaction.response.send_message("Error in view_administrators_handler.", ephemeral=True)
            else:
                 await interaction.followup.send("Error in view_administrators_handler.", ephemeral=True)


    async def assign_alliance_handler(self, interaction: discord.Interaction):
        try:
            with sqlite3.connect('db/settings.sqlite') as settings_db: # Ensure connection is local to method or passed if frequent
                cursor = settings_db.cursor()
                cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
                result = cursor.fetchone()

                if not result or result[0] != 1:
                    await interaction.response.send_message(
                        "❌ Only global administrators can use this command.",
                        ephemeral=True
                    )
                    return

                cursor.execute("""
                    SELECT id, is_initial
                    FROM admin
                    ORDER BY is_initial DESC, id
                """)
                admins = cursor.fetchall()

                if not admins:
                    await interaction.response.send_message(
                        "❌ No administrators found.",
                        ephemeral=True
                    )
                    return

                admin_options = []
                for admin_id, is_initial_val in admins: # Renamed is_initial to avoid conflict
                    try:
                        user = await self.bot.fetch_user(admin_id)
                        admin_name = f"{user.name} ({admin_id})"
                    except Exception as e:
                        admin_name = f"Unknown User ({admin_id})"
                    
                    admin_options.append(
                        discord.SelectOption(
                            label=admin_name[:100],
                            value=str(admin_id),
                            description=f"{'Global Admin' if is_initial_val == 1 else 'Server Admin'}",
                            emoji="👑" if is_initial_val == 1 else "👤"
                        )
                    )

                admin_embed = discord.Embed(
                    title="👤 Admin Selection",
                    description=(
                        "Please select an administrator to assign alliance:\n\n"
                        "**Administrator List**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "Select an administrator from the list below:\n"
                    ),
                    color=discord.Color.blue()
                )

                admin_select = discord.ui.Select(
                    placeholder="Select an administrator...",
                    options=admin_options,
                    custom_id="admin_select_for_assign" # Unique custom_id
                )

                admin_select_view = discord.ui.View(timeout=180) # View for this specific interaction step
                admin_select_view.add_item(admin_select)

                async def assign_admin_select_callback(admin_select_interaction: discord.Interaction): # Renamed
                    try:
                        selected_admin_id = int(admin_select.values[0])
                        
                        # Fetch alliances using self.c_alliance (cog's cursor)
                        self.c_alliance.execute("""
                            SELECT alliance_id, name
                            FROM alliance_list
                            ORDER BY name
                        """)
                        alliances_list = self.c_alliance.fetchall() # Renamed

                        if not alliances_list:
                            await admin_select_interaction.response.send_message( # Use admin_select_interaction
                                "❌ No alliances found.",
                                ephemeral=True
                            )
                            return

                        alliances_with_counts = []
                        for alliance_id_val, name_val in alliances_list: # Renamed
                            with sqlite3.connect('db/users.sqlite') as users_db:
                                users_cursor = users_db.cursor() # Different cursor
                                users_cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id_val,))
                                member_count = users_cursor.fetchone()[0]
                                alliances_with_counts.append((alliance_id_val, name_val, member_count))

                        alliance_embed = discord.Embed(
                            title="🏰 Alliance Selection",
                            description=(
                                "Please select an alliance to assign to the administrator:\n\n"
                                "**Alliance List**\n"
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                "Select an alliance from the list below:\n"
                            ),
                            color=discord.Color.blue()
                        )
                        # AllianceSelectView is defined in alliance_member_operations, ensure it's accessible or redefine/simplify
                        # For this handler, a simple discord.ui.Select might be better if AllianceSelectView is complex or not available.
                        # Assuming AllianceSelectView is accessible and works as a generic alliance selector.
                        alliance_selection_view = AllianceSelectView(alliances_with_counts, self) # Pass self (BotOperations cog)

                        async def assign_alliance_select_callback(alliance_select_interaction: discord.Interaction): # Renamed
                            try:
                                selected_alliance_id = int(alliance_selection_view.current_select.values[0])
                                
                                with sqlite3.connect('db/settings.sqlite') as settings_db_commit: # New connection for commit
                                    cursor_commit = settings_db_commit.cursor()
                                    cursor_commit.execute("""
                                        INSERT INTO adminserver (admin, alliances_id)
                                        VALUES (?, ?)
                                    """, (selected_admin_id, selected_alliance_id))
                                    settings_db_commit.commit()

                                # Fetch names for the success message
                                with sqlite3.connect('db/alliance.sqlite') as alliance_db_fetch: # New connection
                                    cursor_fetch = alliance_db_fetch.cursor()
                                    cursor_fetch.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (selected_alliance_id,))
                                    alliance_name_val = cursor_fetch.fetchone()[0] # Renamed
                                try:
                                    admin_user = await self.bot.fetch_user(selected_admin_id)
                                    admin_name_val = admin_user.name # Renamed
                                except:
                                    admin_name_val = f"Unknown User ({selected_admin_id})"

                                success_embed = discord.Embed(
                                    title="✅ Alliance Assigned",
                                    description=(
                                        f"Successfully assigned alliance to administrator:\n\n"
                                        f"👤 **Administrator:** {admin_name_val}\n"
                                        f"🆔 **Admin ID:** {selected_admin_id}\n"
                                        f"🏰 **Alliance:** {alliance_name_val}\n"
                                        f"🆔 **Alliance ID:** {selected_alliance_id}"
                                    ),
                                    color=discord.Color.green()
                                )
                                
                                await alliance_select_interaction.response.edit_message( # Use alliance_select_interaction
                                    embed=success_embed,
                                    view=None
                                )
                                
                            except Exception as e:
                                if not alliance_select_interaction.response.is_done():
                                    await alliance_select_interaction.response.send_message("Error assigning alliance.", ephemeral=True)
                                else:
                                    await alliance_select_interaction.followup.send("Error assigning alliance.", ephemeral=True)


                        alliance_selection_view.callback = assign_alliance_select_callback
                        
                        await admin_select_interaction.response.edit_message( # Use admin_select_interaction
                            embed=alliance_embed,
                            view=alliance_selection_view
                        )

                    except Exception as e:
                        if not admin_select_interaction.response.is_done():
                            await admin_select_interaction.response.send_message("Error processing admin selection.", ephemeral=True)
                        else:
                             await admin_select_interaction.followup.send("Error processing admin selection.", ephemeral=True)

                admin_select.callback = assign_admin_select_callback

                await interaction.response.send_message( # Initial response for the handler
                    embed=admin_embed,
                    view=admin_select_view,
                    ephemeral=True
                )
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error in assign_alliance_handler.", ephemeral=True)
            else:
                await interaction.followup.send("Error in assign_alliance_handler.", ephemeral=True)


    async def view_admin_permissions_handler(self, interaction: discord.Interaction):
        try:
            with sqlite3.connect('db/settings.sqlite') as settings_db: # Local connection
                cursor = settings_db.cursor()
                cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
                result = cursor.fetchone()
                
                if not result or result[0] != 1:
                    await interaction.response.send_message(
                        "❌ Only global administrators can use this command.", 
                        ephemeral=True
                    )
                    return

                with sqlite3.connect('db/alliance.sqlite') as alliance_db: # Local connection
                    alliance_cursor = alliance_db.cursor()

                    cursor.execute("""
                        SELECT a.id, a.is_initial, admin_server.alliances_id
                        FROM admin a
                        JOIN adminserver admin_server ON a.id = admin_server.admin
                        ORDER BY a.is_initial DESC, a.id
                    """)
                    admin_permissions = cursor.fetchall()

                    if not admin_permissions:
                        await interaction.response.send_message(
                            "No admin permissions found.",
                            ephemeral=True
                        )
                        return

                    admin_alliance_info = []
                    for admin_id, is_initial_val, alliance_id_val in admin_permissions: # Renamed
                        alliance_cursor.execute("""
                            SELECT name FROM alliance_list
                            WHERE alliance_id = ?
                        """, (alliance_id_val,))
                        alliance_result = alliance_cursor.fetchone()
                        if alliance_result:
                            admin_alliance_info.append((admin_id, is_initial_val, alliance_id_val, alliance_result[0]))

                    embed = discord.Embed(
                        title="👥 Admin Alliance Permissions",
                        description=(
                            "Select an admin's permission to remove it:\n\n" # Modified description
                            "**Admin Permissions List**\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                        ),
                        color=discord.Color.blue()
                    )

                    options = []
                    # Need to store admin_name and alliance_name for the confirmation message
                    # This could be done by fetching them again in the select callback, or storing temporarily
                    # For simplicity here, we'll re-fetch in callback if needed, or pass enough info in value.

                    temp_permission_details = {} # Store details for callback

                    for p_admin_id, p_is_initial, p_alliance_id, p_alliance_name in admin_alliance_info:
                        try:
                            user = await interaction.client.fetch_user(p_admin_id)
                            p_admin_name = user.name
                        except:
                            p_admin_name = f"Unknown User ({p_admin_id})"

                        option_label = f"{p_admin_name[:40]} - {p_alliance_name[:40]}"
                        option_value = f"{p_admin_id}:{p_alliance_id}"
                        temp_permission_details[option_value] = {"admin_name": p_admin_name, "alliance_name": p_alliance_name}

                        options.append(
                            discord.SelectOption(
                                label=option_label,
                                value=option_value,
                                description=f"Admin ID: {p_admin_id}, Alliance ID: {p_alliance_id}",
                                emoji="👑" if p_is_initial == 1 else "👤"
                            )
                        )

                    if not options:
                        await interaction.response.send_message(
                            "No admin-alliance permissions found to display.",
                            ephemeral=True
                        )
                        return

                    perm_select = discord.ui.Select( # Renamed variable
                        placeholder="Select an admin/alliance permission to remove...",
                        options=options,
                        custom_id="admin_permission_select_remove" # Unique custom_id
                    )

                    async def remove_permission_select_callback(select_interaction: discord.Interaction): # Renamed
                        try:
                            selected_value = select_interaction.data["values"][0]
                            admin_id_str, alliance_id_str = selected_value.split(":")

                            # Retrieve stored details for confirmation message
                            details = temp_permission_details.get(selected_value, {})
                            confirm_admin_name = details.get("admin_name", f"Admin ID {admin_id_str}")
                            confirm_alliance_name = details.get("alliance_name", f"Alliance ID {alliance_id_str}")

                            confirm_embed = discord.Embed(
                                title="⚠️ Confirm Permission Removal",
                                description=(
                                    f"Are you sure you want to remove this alliance permission?\n\n"
                                    f"**Admin:** {confirm_admin_name} ({admin_id_str})\n"
                                    f"**Alliance:** {confirm_alliance_name} ({alliance_id_str})"
                                ),
                                color=discord.Color.yellow()
                            )

                            confirm_buttons_view = discord.ui.View(timeout=60) # Renamed

                            async def confirm_remove_action_callback(button_interaction: discord.Interaction): # Renamed
                                try:
                                    # Re-establish connection for write operation if necessary, or use self.settings_cursor directly
                                    with sqlite3.connect('db/settings.sqlite') as s_db:
                                        s_cur = s_db.cursor()
                                        s_cur.execute("""
                                            DELETE FROM adminserver
                                            WHERE admin = ? AND alliances_id = ?
                                        """, (int(admin_id_str), int(alliance_id_str)))
                                        s_db.commit()

                                    success_embed = discord.Embed(
                                        title="✅ Permission Removed",
                                        description=(
                                            f"Successfully removed alliance permission:\n\n"
                                            f"**Admin:** {confirm_admin_name} ({admin_id_str})\n"
                                            f"**Alliance:** {confirm_alliance_name} ({alliance_id_str})"
                                        ),
                                        color=discord.Color.green()
                                    )
                                    await button_interaction.response.edit_message(
                                        embed=success_embed,
                                        view=None
                                    )
                                except Exception as e:
                                    await button_interaction.response.send_message("Error removing permission.",ephemeral=True)


                            async def cancel_remove_action_callback(button_interaction: discord.Interaction): # Renamed
                                cancel_embed = discord.Embed(
                                    title="❌ Operation Cancelled",
                                    description="Permission removal has been cancelled.",
                                    color=discord.Color.red()
                                )
                                await button_interaction.response.edit_message(
                                    embed=cancel_embed,
                                    view=None
                                )

                            confirm_btn = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_perm_remove_action")
                            cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_perm_remove_action")
                            confirm_btn.callback = confirm_remove_action_callback
                            cancel_btn.callback = cancel_remove_action_callback
                            confirm_buttons_view.add_item(confirm_btn)
                            confirm_buttons_view.add_item(cancel_btn)

                            await select_interaction.response.edit_message( # Edit the message from the select
                                embed=confirm_embed,
                                view=confirm_buttons_view
                            )

                        except Exception as e:
                            await select_interaction.response.send_message("Error processing selection.",ephemeral=True)

                    perm_select.callback = remove_permission_select_callback

                    perm_view = discord.ui.View(timeout=180) # Renamed
                    perm_view.add_item(perm_select)

                    await interaction.response.send_message(embed=embed, view=perm_view, ephemeral=True) # Initial response

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error in view_admin_permissions_handler.", ephemeral=True)
            else:
                await interaction.followup.send("Error in view_admin_permissions_handler.", ephemeral=True)


    async def transfer_old_database_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()

            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command.",
                    ephemeral=True
                )
                return

            database_cog = self.bot.get_cog('DatabaseTransfer') # Assuming cog name is 'DatabaseTransfer'
            if database_cog and hasattr(database_cog, 'transfer_old_database'):
                await database_cog.transfer_old_database(interaction) # This method should handle its own responses
            else:
                await interaction.response.send_message(
                    "❌ Database transfer module not loaded or method not found.",
                    ephemeral=True
                )

        except Exception as e:
            if not interaction.response.is_done():
                 await interaction.response.send_message("Error in transfer_old_database_handler.", ephemeral=True)
            else:
                 await interaction.followup.send("Error in transfer_old_database_handler.", ephemeral=True)


    async def check_updates_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()

            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command.",
                    ephemeral=True
                )
                return

            current_version, new_version, update_notes, updates_needed = await self.check_for_updates()

            if not current_version or not new_version: # check_for_updates might return None for these
                await interaction.response.send_message(
                    "❌ Failed to check for updates. Please try again later.",
                    ephemeral=True
                )
                return

            main_embed = discord.Embed(
                title="🔄 Bot Update Status",
                color=discord.Color.blue() if not updates_needed else discord.Color.yellow()
            )

            main_embed.add_field(
                name="Current Version",
                value=f"`{current_version}`",
                inline=True
            )

            main_embed.add_field(
                name="Latest Version",
                value=f"`{new_version}`",
                inline=True
            )

            if updates_needed:
                main_embed.add_field(
                    name="Status",
                    value="🔄 **Update Available**",
                    inline=True
                )

                if update_notes:
                    notes_text = "\n".join([f"• {note.lstrip('- *•').strip()}" for note in update_notes[:10]])
                    if len(update_notes) > 10:
                        notes_text += f"\n• ... and more!"

                    main_embed.add_field(
                        name="Release Notes",
                        value=notes_text[:1024],
                        inline=False
                    )

                main_embed.add_field(
                    name="How to Update",
                    value=(
                        "To update to the new version:\n"
                        "🔄 **Restart the bot** (main.py)\n"
                        "✅ Accept the update when prompted\n\n"
                        "The bot will automatically download and install the update."
                    ),
                    inline=False
                )
            else:
                main_embed.add_field(
                    name="Status",
                    value="✅ **Up to Date**",
                    inline=True
                )
                main_embed.description = "Your bot is running the latest version!"

            await interaction.response.send_message( # Send as new message
                embed=main_embed,
                ephemeral=True
            )

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error in check_updates_handler.", ephemeral=True)
            else:
                await interaction.followup.send("Error in check_updates_handler.", ephemeral=True)


    async def alliance_control_messages_handler(self, interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            result = self.settings_cursor.fetchone()

            if not result or result[0] != 1:
                await interaction.response.send_message(
                    "❌ Only global administrators can use this command.",
                    ephemeral=True
                )
                return

            self.settings_cursor.execute("SELECT value FROM auto LIMIT 1") # Assuming 'auto' table exists
            auto_result = self.settings_cursor.fetchone()
            current_value = auto_result[0] if auto_result else 1 # Default to 1 (On) if not set

            embed = discord.Embed(
                title="💬 Alliance Control Messages Settings",
                description=f"Alliance Control Information Message is Currently {'On' if current_value == 1 else 'Off'}",
                color=discord.Color.green() if current_value == 1 else discord.Color.red()
            )

            control_msg_view = discord.ui.View(timeout=180) # Renamed view
            
            open_button = discord.ui.Button(
                label="Turn On",
                emoji="✅",
                style=discord.ButtonStyle.success,
                custom_id="control_messages_open_action", # Unique custom_id
                disabled=current_value == 1
            )

            close_button = discord.ui.Button(
                label="Turn Off",
                emoji="❌",
                style=discord.ButtonStyle.danger,
                custom_id="control_messages_close_action", # Unique custom_id
                disabled=current_value == 0
            )

            async def open_action_callback(button_interaction: discord.Interaction): # Renamed
                self.settings_cursor.execute("UPDATE auto SET value = 1") # Ensure 'auto' table exists and has 'value' column
                self.settings_db.commit()

                embed.description = "Alliance Control Information Message Turned On"
                embed.color = discord.Color.green()

                open_button.disabled = True
                close_button.disabled = False

                await button_interaction.response.edit_message(embed=embed, view=control_msg_view)

            async def close_action_callback(button_interaction: discord.Interaction): # Renamed
                self.settings_cursor.execute("UPDATE auto SET value = 0") # Ensure 'auto' table
                self.settings_db.commit()

                embed.description = "Alliance Control Information Message Turned Off"
                embed.color = discord.Color.red()

                open_button.disabled = False
                close_button.disabled = True

                await button_interaction.response.edit_message(embed=embed, view=control_msg_view)

            open_button.callback = open_action_callback
            close_button.callback = close_action_callback

            control_msg_view.add_item(open_button)
            control_msg_view.add_item(close_button)

            await interaction.response.send_message(embed=embed, view=control_msg_view, ephemeral=True) # Send as new message

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error in alliance_control_messages_handler.", ephemeral=True)
            else:
                await interaction.followup.send("Error in alliance_control_messages_handler.", ephemeral=True)


    def get_current_version(self):
        """Get current version from version file"""
        try:
            if os.path.exists("version"):
                with open("version", "r") as f:
                    return f.read().strip()
            return "v0.0.0"
        except Exception:
            return "v0.0.0"

    def setup_database(self):
        try:
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY,
                    is_initial INTEGER DEFAULT 0
                )
            """)

            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS adminserver (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin INTEGER NOT NULL,
                    alliances_id INTEGER NOT NULL,
                    FOREIGN KEY (admin) REFERENCES admin(id),
                    UNIQUE(admin, alliances_id)
                )
            """)

            self.settings_db.commit()

        except Exception as e:
            pass

    def __del__(self):
        try:
            self.settings_db.close()
            self.alliance_db.close()
        except:
            pass

    # @commands.Cog.listener() # Comment out or remove if no other component interactions
    # async def on_interaction(self, interaction: discord.Interaction):
    #     if not interaction.type == discord.InteractionType.component:
    #         return
    #     # Remove all the logic for custom_ids now handled by BotOperationsView
    #     # Keep only logic for other components if any, otherwise remove method.


    async def show_bot_operations_menu(self, interaction: discord.Interaction, target_guild: Optional[discord.Guild]):
        embed_description = (
            "Please choose an operation:\n\n"
            "**Available Operations**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👥 **Admin Management**\n"
            "└ Manage bot administrators\n\n"
            "🔍 **Admin Permissions**\n"
            "└ View and manage admin permissions\n\n"
            "🔄 **Bot Updates**\n"
            "└ Check and manage updates\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed = discord.Embed(
            title="🤖 Bot Operations",
            description=embed_description.replace('\n', '\n'),
            color=discord.Color.blue()
        )

        view = BotOperationsView(self, target_guild_id=target_guild.id if target_guild else None)

        # This method is called from cogs/alliance.py's on_interaction,
        # which should be an edit_message context.
        if interaction.response.is_done():
            # If the interaction was already responded to (e.g. by a defer in alliance.py, or prompt_selection)
            # we should use edit_original_response or followup.
            # Since this is typically replacing the content of the message from alliance settings,
            # edit_original_response is appropriate.
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            # This case would occur if show_bot_operations_menu was called as the first response to an interaction.
            # Given it's a sub-menu, edit_message is generally preferred for component interactions.
            # If this was a slash command, interaction.response.send_message would be the first call.
            # For consistency with how it's called from alliance.py (as an edit to an existing message),
            # edit_message is the target. If it's not done, it implies this is the first actual modification
            # to the message for this specific interaction component.
            await interaction.response.edit_message(embed=embed, view=view)
        # Simplified error handling for the subtask, assuming the primary goal is view replacement.
        # A more robust error handling would go here.
        # except Exception as e:
        #     if not any(error_code in str(e) for error_code in ["10062", "40060"]):
                print(f"Show bot operations menu error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while showing the menu.",
                    ephemeral=True
                )

    async def confirm_permission_removal(self, admin_id: int, alliance_id: int, confirm_interaction: discord.Interaction):
        try:
            self.settings_cursor.execute("""
                DELETE FROM adminserver 
                WHERE admin = ? AND alliances_id = ?
            """, (admin_id, alliance_id))
            self.settings_db.commit()
            return True
        except Exception as e:
            return False

    async def check_for_updates(self):
        """Check for updates using GitHub releases API"""
        try:
            latest_release_url = "https://api.github.com/repos/whiteout-project/bot/releases/latest"
            
            response = requests.get(latest_release_url, timeout=10)
            if response.status_code != 200:
                return None, None, [], False

            latest_release_data = response.json()
            latest_tag = latest_release_data.get("tag_name", "")
            current_version = self.get_current_version()
            
            if not latest_tag:
                return current_version, None, [], False

            updates_needed = current_version != latest_tag
            
            # Parse release notes
            update_notes = []
            release_body = latest_release_data.get("body", "")
            if release_body:
                for line in release_body.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                        update_notes.append(line)

            return current_version, latest_tag, update_notes, updates_needed

        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None, None, [], False

async def setup(bot):
    await bot.add_cog(BotOperations(bot, sqlite3.connect('db/settings.sqlite'))) 
