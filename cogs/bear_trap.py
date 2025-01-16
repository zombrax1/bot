import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
import pytz
import os
import asyncio

class BearTrap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db_path = 'db/beartime.sqlite'
        os.makedirs('db', exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bear_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                hour INTEGER NOT NULL,
                minute INTEGER NOT NULL,
                timezone TEXT NOT NULL,
                description TEXT NOT NULL,
                notification_type INTEGER NOT NULL,
                mention_type TEXT NOT NULL,
                repeat_enabled INTEGER NOT NULL DEFAULT 0,
                repeat_minutes INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL,
                last_notification TIMESTAMP,
                next_notification TIMESTAMP
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER NOT NULL,
                notification_time INTEGER NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES bear_notifications(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()

    async def cog_load(self):

        self.notification_task = asyncio.create_task(self.check_notifications())

    async def cog_unload(self):

        if hasattr(self, 'notification_task'):
            self.notification_task.cancel()

    async def save_notification(self, guild_id: int, channel_id: int, start_date: datetime,
                              hour: int, minute: int, timezone: str, description: str,
                              created_by: int, notification_type: int, mention_type: str,
                              repeat_48h: bool, repeat_minutes: int = 0) -> int:
        try:

            tz = pytz.timezone(timezone)
            next_notification = start_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
                tzinfo=tz
            )

            self.cursor.execute("""
                INSERT INTO bear_notifications 
                (guild_id, channel_id, hour, minute, timezone, description, notification_type,
                mention_type, repeat_enabled, repeat_minutes, created_by, next_notification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, hour, minute, timezone, description, notification_type,
                mention_type, 1 if repeat_48h else 0, repeat_minutes, created_by,
                next_notification.isoformat()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error saving notification: {e}")
            raise

    async def check_notifications(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:

                self.cursor.execute("""
                    SELECT * FROM bear_notifications 
                    WHERE is_enabled = 1 AND next_notification IS NOT NULL
                """)
                notifications = self.cursor.fetchall()

                now = datetime.now(pytz.UTC)
                for notification in notifications:
                    try:
                        await self.process_notification(notification)
                    except Exception as e:
                        print(f"Error processing notification {notification[0]}: {e}")
                        continue

            except Exception as e:
                print(f"Error in notification checker: {e}")

            await asyncio.sleep(0.1)

    async def process_notification(self, notification):
        try:
            (id, guild_id, channel_id, hour, minute, timezone, description,
             notification_type, mention_type, repeat_enabled, repeat_minutes,
             is_enabled, created_at, created_by, last_notification,
             next_notification) = notification
            
            if not is_enabled:
                return

            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"Channel {channel_id} not found")
                return

            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            next_time = datetime.fromisoformat(next_notification)

            if next_time < now and repeat_enabled and repeat_minutes > 0:
                time_diff = (now - next_time).total_seconds() / 60
                periods_passed = int(time_diff / repeat_minutes) + 1
                next_time = next_time + timedelta(minutes=repeat_minutes * periods_passed)
                
                self.cursor.execute("""
                    UPDATE bear_notifications 
                    SET next_notification = ? 
                    WHERE id = ?
                """, (next_time.isoformat(), id))
                self.conn.commit()
                return

            time_until = next_time - now
            minutes_until = time_until.total_seconds() / 60

            if time_until.total_seconds() < -0.1:
                return

            notification_times = []
            
            if notification_type == 1:  
                notification_times = [30, 10, 5, 0]
            elif notification_type == 2:  
                notification_times = [10, 5, 0]
            elif notification_type == 3:  
                notification_times = [5, 0]
            elif notification_type == 4:  
                notification_times = [5]
            elif notification_type == 5:  
                notification_times = [0]
            elif notification_type == 6:  
                if description.startswith("CUSTOM_TIMES:"):
                    times_str = description.split("CUSTOM_TIMES:")[1].split("|")[0]
                    notification_times = [int(t) for t in times_str.split('-')]
                    description = description.split("|")[1]

            should_notify = False
            current_time = None

            for notify_time in notification_times:
                time_diff = abs(minutes_until - notify_time)
                if time_diff < 0.1:  

                    thirty_seconds_ago = (now - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM notification_history 
                        WHERE notification_id = ? 
                        AND notification_time = ? 
                        AND sent_at >= ?
                    """, (id, notify_time, thirty_seconds_ago))
                    
                    count = self.cursor.fetchone()[0]
                    if count == 0:  
                        should_notify = True
                        current_time = notify_time
                    break

            if should_notify:
                mention_text = ""
                if mention_type == "everyone":
                    mention_text = "@everyone"
                elif mention_type.startswith("role_"):
                    role_id = int(mention_type.split("_")[1])
                    role = channel.guild.get_role(role_id)
                    if role:
                        mention_text = role.mention
                    else:
                        mention_text = f"Role {role_id}"
                elif mention_type.startswith("member_"):
                    member_id = int(mention_type.split("_")[1])
                    member = await channel.guild.fetch_member(member_id)
                    if member:
                        mention_text = member.mention
                    else:
                        mention_text = f"Member {member_id}"

                rounded_time = round(minutes_until)
                if rounded_time > 0:
                    await channel.send(f"{mention_text} ⏰ **{description}** will start in **{rounded_time}** minutes!")
                else:
                    await channel.send(f"{mention_text} ⏰ **{description}** ")

                current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                self.cursor.execute("""
                    INSERT INTO notification_history (notification_id, notification_time, sent_at)
                    VALUES (?, ?, ?)
                """, (id, current_time, current_time_str))

                self.cursor.execute("""
                    UPDATE bear_notifications 
                    SET last_notification = ? 
                    WHERE id = ?
                """, (now.isoformat(), id))

                if rounded_time == 0:
                    if repeat_enabled and repeat_minutes > 0:
                        current_next = datetime.fromisoformat(next_notification)
                        next_time = current_next + timedelta(minutes=repeat_minutes)

                        self.cursor.execute("""
                            UPDATE bear_notifications 
                            SET next_notification = ? 
                            WHERE id = ?
                        """, (next_time.isoformat(), id))
                    else:
                        self.cursor.execute("""
                            UPDATE bear_notifications 
                            SET is_enabled = 0 
                            WHERE id = ?
                        """, (id,))
                
                self.conn.commit()
                
        except Exception as e:
            print(f"Error processing notification: {e}")
            import traceback
            traceback.print_exc()

    async def get_notifications(self, guild_id: int) -> list:
        try:
            self.cursor.execute("""
                SELECT * FROM bear_notifications 
                WHERE guild_id = ? 
                ORDER BY next_notification
            """, (guild_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    async def toggle_notification(self, notification_id: int, enabled: bool) -> bool:
        try:

            self.cursor.execute("""
                SELECT is_enabled FROM bear_notifications WHERE id = ?
            """, (notification_id,))
            result = self.cursor.fetchone()
            if not result:
                return False

            self.cursor.execute("""
                UPDATE bear_notifications 
                SET is_enabled = ? 
                WHERE id = ?
            """, (1 if enabled else 0, notification_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error toggling notification: {e}")
            return False

    def get_world_times(self):
        current_utc = datetime.now(pytz.UTC)
        times = {
            "UTC": current_utc,
            "US/Pacific": current_utc.astimezone(pytz.timezone('US/Pacific')),
            "US/Eastern": current_utc.astimezone(pytz.timezone('US/Eastern')),
            "Europe/London": current_utc.astimezone(pytz.timezone('Europe/London')),
            "Europe/Istanbul": current_utc.astimezone(pytz.timezone('Europe/Istanbul')),
            "Asia/Tokyo": current_utc.astimezone(pytz.timezone('Asia/Tokyo')),
        }
        return times
    async def show_bear_trap_menu(self, interaction: discord.Interaction):
        try:
            times = self.get_world_times()
            time_display = "\n".join([
                f"🌍 **{zone}:** {time.strftime('%H:%M:%S')}"
                for zone, time in times.items()
            ])
            
            embed = discord.Embed(
                title="🐻 Bear Trap System",
                description=(
                    "Configure time notification settings:\n\n"
                    "**Current World Times**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{time_display}\n\n"
                    "**Available Operations**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "⏰ **Set Time**\n"
                    "└ Configure notification time\n"
                    "└ Not just for Bear! Use it for any event:\n"
                    "   Bear - KE - Forst - CJ and everything else\n"
                    "└ Add unlimited notifications\n\n"
                    "🗑️ **Remove Notification**\n"
                    "└ Delete unwanted notifications\n\n"
                    "✅ **Enable/Disable**\n"
                    "└ Toggle notifications\n\n"
                    "📋 **View Settings**\n"
                    "└ Check current configuration\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=discord.Color.gold()
            )

            embed.set_footer(text="Last Updated")
            embed.timestamp = datetime.now()
            
            view = BearTrapView(self)
            
            try:
                await interaction.response.edit_message(embed=embed, view=view)
            except discord.InteractionResponded:
                pass
                
        except Exception as e:
            print(f"Error in show_bear_trap_menu: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )

    async def check_admin(self, interaction: discord.Interaction) -> bool:
        try:
            conn = sqlite3.connect('db/settings.sqlite')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM admin WHERE id = ?", (interaction.user.id,))
            is_admin = cursor.fetchone() is not None
            conn.close()
            
            if not is_admin:
                await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
                return False
            return True
        except Exception as e:
            print(f"Error in admin check: {e}")
            return False

class TimeSelectModal(discord.ui.Modal, title="Set Notification Time"):
    def __init__(self, cog: BearTrap):
        super().__init__()
        self.cog = cog
        
        current_utc = datetime.now(pytz.UTC)
        
        self.start_date = discord.ui.TextInput(
            label="Start Date (DD/MM/YYYY)",
            placeholder="Enter start date (e.g., 25/03/2024)",
            min_length=8,
            max_length=10,
            required=True,
            default=current_utc.strftime("%d/%m/%Y")
        )
        self.add_item(self.start_date)
        
        self.hour = discord.ui.TextInput(
            label="Hour (0-23)",
            placeholder="Enter hour (e.g., 14)",
            min_length=1,
            max_length=2,
            required=True,
            default=current_utc.strftime("%H")
        )
        self.add_item(self.hour)
        
        self.minute = discord.ui.TextInput(
            label="Minute (0-59)",
            placeholder="Enter minute (e.g., 30)",
            min_length=1,
            max_length=2,
            required=True,
            default=current_utc.strftime("%M")
        )
        self.add_item(self.minute)
        
        self.timezone = discord.ui.TextInput(
            label="Timezone",
            placeholder="Enter timezone (e.g., UTC, Europe/Istanbul)",
            min_length=1,
            max_length=50,
            required=True,
            default="UTC"
        )
        self.add_item(self.timezone)
        
        self.description = discord.ui.TextInput(
            label="Notification Description",
            placeholder="Enter description for this notification",
            min_length=1,
            max_length=100,
            required=True,
            style=discord.TextStyle.long
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        try:

            try:
                timezone = pytz.timezone(self.timezone.value)
            except pytz.exceptions.UnknownTimeZoneError:
                await interaction.response.send_message(
                    "❌ Invalid timezone! Please use a valid timezone (e.g., UTC, Europe/Istanbul).",
                    ephemeral=True
                )
                return

            try:
                start_date = datetime.strptime(self.start_date.value, "%d/%m/%Y")

                now = datetime.now(timezone)

                start_date = timezone.localize(start_date)
                
                if start_date.date() < now.date():
                    await interaction.response.send_message(
                        "❌ Start date cannot be in the past for the selected timezone!",
                        ephemeral=True
                    )
                    return
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid date format! Please use DD/MM/YYYY format.",
                    ephemeral=True
                )
                return

            hour = int(self.hour.value)
            minute = int(self.minute.value)
            
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time format")

            channels = interaction.guild.text_channels
            await self.show_channel_selection(
                interaction, 
                start_date,
                hour, 
                minute, 
                self.timezone.value, 
                self.description.value, 
                channels
            )

        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time format! Please use numbers for hour (0-23) and minute (0-59).",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in time modal: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting the time.",
                ephemeral=True
            )

    async def show_channel_selection(self, interaction, start_date, hour, minute, timezone, description, channels):
        total_pages = (len(channels) - 1) // 25 + 1
        embed = discord.Embed(
            title="📢 Select Notification Channel",
            description=(
                "**Selected Time Settings**\n"
                f"📅 Start Date: {start_date.strftime('%d/%m/%Y')}\n"
                f"⏰ Time: {hour:02d}:{minute:02d} {timezone}\n"
                f"📝 Description: {description}\n\n"
                "Please select a channel for notifications:\n"
                f"Total Channels: {len(channels)} | Page 1/{total_pages}"
            ),
            color=discord.Color.blue()
        )

        view = PaginatedChannelSelectView(
            self.cog, 
            start_date,
            hour, 
            minute, 
            timezone, 
            description, 
            channels
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PaginatedChannelSelectView(discord.ui.View):
    def __init__(self, cog, start_date, hour, minute, timezone, description, channels):
        super().__init__(timeout=300)
        self.cog = cog
        self.start_date = start_date
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.description = description
        self.channels = channels
        self.current_page = 0
        self.items_per_page = 25
        self.total_pages = (len(channels) - 1) // self.items_per_page + 1
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.channels))
        current_channels = self.channels[start_idx:end_idx]

        select = discord.ui.Select(
            placeholder=f"Select a channel (Page {self.current_page + 1}/{self.total_pages})",
            options=[
                discord.SelectOption(
                    label=channel.name[:25],
                    value=str(channel.id),
                    description=f"Channel ID: {channel.id}"
                ) for channel in current_channels
            ]
        )
        select.callback = self.channel_selected
        self.add_item(select)

        if len(self.channels) > self.items_per_page:
            if self.current_page > 0:
                prev_button = discord.ui.Button(label="Previous Page", emoji="◀️", custom_id="prev")
                prev_button.callback = self.previous_page
                self.add_item(prev_button)

            if (self.current_page + 1) * self.items_per_page < len(self.channels):
                next_button = discord.ui.Button(label="Next Page", emoji="▶️", custom_id="next")
                next_button.callback = self.next_page
                self.add_item(next_button)

    async def previous_page(self, interaction):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        
        embed = interaction.message.embeds[0]
        embed.description = embed.description.split("\n")
        embed.description[-1] = f"Total Channels: {len(self.channels)} | Page {self.current_page + 1}/{self.total_pages}"
        embed.description = "\n".join(embed.description)
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_page(self, interaction):
        max_pages = (len(self.channels) - 1) // self.items_per_page
        self.current_page = min(max_pages, self.current_page + 1)
        self.update_buttons()
        
        embed = interaction.message.embeds[0]
        embed.description = embed.description.split("\n")
        embed.description[-1] = f"Total Channels: {len(self.channels)} | Page {self.current_page + 1}/{self.total_pages}"
        embed.description = "\n".join(embed.description)
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def channel_selected(self, interaction):
        channel_id = int(interaction.data["values"][0])

        embed = discord.Embed(
            title="⏰ Select Notification Type",
            description=(
                "Choose when to send notifications:\n\n"
                "1️⃣ 30min, 10min, 5min and Time's up\n"
                "2️⃣ 10min, 5min and Time's up\n"
                "3️⃣ 5min and Time's up\n"
                "4️⃣ Only 5min before\n"
                "5️⃣ Only at Time's up"
            ),
            color=discord.Color.blue()
        )

        view = NotificationTypeView(
            self.cog,
            self.start_date,
            self.hour,
            self.minute,
            self.timezone,
            self.description,
            channel_id
        )
        await interaction.response.edit_message(embed=embed, view=view)

class NotificationTypeView(discord.ui.View):
    def __init__(self, cog, start_date, hour, minute, timezone, description, channel_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.start_date = start_date
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.description = description
        self.channel_id = channel_id

    @discord.ui.button(label="30m, 10m, 5m & Time", style=discord.ButtonStyle.primary, custom_id="type_1", row=0)
    async def type_1(self, interaction, button):
        await self.show_mention_options(interaction, 1)

    @discord.ui.button(label="10m, 5m & Time", style=discord.ButtonStyle.primary, custom_id="type_2", row=0)
    async def type_2(self, interaction, button):
        await self.show_mention_options(interaction, 2)

    @discord.ui.button(label="5m & Time", style=discord.ButtonStyle.primary, custom_id="type_3", row=1)
    async def type_3(self, interaction, button):
        await self.show_mention_options(interaction, 3)

    @discord.ui.button(label="Only 5m", style=discord.ButtonStyle.primary, custom_id="type_4", row=1)
    async def type_4(self, interaction, button):
        await self.show_mention_options(interaction, 4)

    @discord.ui.button(label="Only Time", style=discord.ButtonStyle.primary, custom_id="type_5", row=1)
    async def type_5(self, interaction, button):
        await self.show_mention_options(interaction, 5)

    @discord.ui.button(label="Custom Times", style=discord.ButtonStyle.success, custom_id="type_6", row=2)
    async def type_6(self, interaction, button):
        modal = CustomTimesModal(self.cog, self.start_date, self.hour, self.minute, self.timezone, self.description, self.channel_id)
        await interaction.response.send_modal(modal)

    async def show_mention_options(self, interaction, notification_type):
        embed = discord.Embed(
            title="📢 Select Mention Type",
            description=(
                "Choose how to mention users:\n\n"
                "1️⃣ @everyone\n"
                "2️⃣ Specific Role"
            ),
            color=discord.Color.blue()
        )

        view = MentionTypeView(
            self.cog,
            self.start_date,
            self.hour,
            self.minute,
            self.timezone,
            self.description,
            self.channel_id,
            notification_type
        )
        await interaction.response.edit_message(embed=embed, view=view)

class CustomTimesModal(discord.ui.Modal, title="Set Custom Notification Times"):
    def __init__(self, cog, start_date, hour, minute, timezone, description, channel_id):
        super().__init__()
        self.cog = cog
        self.start_date = start_date
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.description = description
        self.channel_id = channel_id
        
        self.custom_times = discord.ui.TextInput(
            label="Custom Notification Times",
            placeholder="Enter times in minutes (e.g., 60-20-15-4-2 or 60-20-15-4-2-0)",
            min_length=1,
            max_length=50,
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.custom_times)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            times_str = self.custom_times.value.strip()
            times = [int(t) for t in times_str.split('-')]
            
            if not all(isinstance(t, int) and t >= 0 for t in times):
                raise ValueError("All times must be non-negative integers")
                
            if not times:
                raise ValueError("At least one time must be specified")
                
            if not all(times[i] > times[i+1] for i in range(len(times)-1)):
                raise ValueError("Times must be in descending order")

            embed = discord.Embed(
                title="📢 Select Mention Type",
                description=(
                    "Choose how to mention users:\n\n"
                    "1️⃣ @everyone\n"
                    "2️⃣ Specific Role"
                ),
                color=discord.Color.blue()
            )

            view = MentionTypeView(
                self.cog,
                self.start_date,
                self.hour,
                self.minute,
                self.timezone,
                self.description,
                self.channel_id,
                6,  
                custom_times=times  
            )
            await interaction.response.edit_message(embed=embed, view=view)

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid input: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in custom times modal: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing custom times.",
                ephemeral=True
            )

class MentionTypeView(discord.ui.View):
    def __init__(self, cog, start_date, hour, minute, timezone, description, channel_id, notification_type, custom_times=None):
        super().__init__(timeout=300)
        self.cog = cog
        self.start_date = start_date
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.description = description
        self.channel_id = channel_id
        self.notification_type = notification_type
        self.custom_times = custom_times

    @discord.ui.button(label="@everyone", emoji="👥", style=discord.ButtonStyle.primary, custom_id="everyone", row=0)
    async def everyone_button(self, interaction, button):
        await self.show_repeat_option(interaction, "everyone")

    @discord.ui.button(label="Select Role", emoji="🎭", style=discord.ButtonStyle.primary, custom_id="role", row=0)
    async def role_button(self, interaction, button):
        roles = interaction.guild.roles
        options = [
            discord.SelectOption(
                label=role.name[:25],
                value=str(role.id),
                description=f"Role ID: {role.id}"
            ) for role in roles if role.name != "@everyone"
        ]

        select = discord.ui.Select(
            placeholder="Select a role to mention",
            options=options[:25]
        )

        async def role_selected(role_interaction):
            role_id = int(role_interaction.data["values"][0])
            await self.show_repeat_option(role_interaction, f"role_{role_id}")

        select.callback = role_selected
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="👥 Select Role",
                description="Choose a role to mention:",
                color=discord.Color.blue()
            ),
            view=view
        )

    @discord.ui.button(label="Select Member", emoji="👤", style=discord.ButtonStyle.primary, custom_id="member", row=1)
    async def member_button(self, interaction, button):
        prompt_message = await interaction.response.send_message(
            "Please mention the member you want to notify by replying with @username",
            ephemeral=True
        )

        def check(message):
            return message.author.id == interaction.user.id and len(message.mentions) > 0

        try:
            message = await self.cog.bot.wait_for('message', timeout=30.0, check=check)
            member = message.mentions[0]
            await message.delete()

            await interaction.delete_original_response()

            embed = discord.Embed(
                title="🔄 Repeat Settings",
                description=(
                    "**Configure Notification Repeat**\n\n"
                    "Choose how often you want this notification to repeat:\n\n"
                    "• No Repeat: Notification will be sent only once\n"
                    "• Custom Interval: Set a custom repeat interval (minutes/hours/days/weeks/months)"
                ),
                color=discord.Color.blue()
            )

            view = RepeatOptionView(
                self.cog,
                self.start_date,
                self.hour,
                self.minute,
                self.timezone,
                self.description,
                self.channel_id,
                self.notification_type,
                f"member_{member.id}"
            )
            
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=view
            )
            
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "❌ No member was mentioned within 30 seconds. Please try again.",
                ephemeral=True
            )

    async def show_repeat_option(self, interaction, mention_type):
        embed = discord.Embed(
            title="🔄 Repeat Settings",
            description=(
                "**Configure Notification Repeat**\n\n"
                "Choose how often you want this notification to repeat:\n\n"
                "• No Repeat: Notification will be sent only once\n"
                "• Custom Interval: Set a custom repeat interval (minutes/hours/days/weeks/months)"
            ),
            color=discord.Color.blue()
        )

        if self.notification_type == 6:
            formatted_description = f"CUSTOM_TIMES:{'-'.join(map(str, self.custom_times))}|{self.description}"
        else:
            formatted_description = self.description

        view = RepeatOptionView(
            self.cog,
            self.start_date,
            self.hour,
            self.minute,
            self.timezone,
            formatted_description,
            self.channel_id,
            self.notification_type,
            mention_type
        )
        await interaction.response.edit_message(embed=embed, view=view)

class RepeatOptionView(discord.ui.View):
    def __init__(self, cog, start_date, hour, minute, timezone, description, channel_id, notification_type, mention_type):
        super().__init__(timeout=300)
        self.cog = cog
        self.start_date = start_date
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.description = description
        self.channel_id = channel_id
        self.notification_type = notification_type
        self.mention_type = mention_type

    @discord.ui.button(label="No Repeat", emoji="❌", style=discord.ButtonStyle.danger, custom_id="no_repeat")
    async def no_repeat_button(self, interaction, button):
        await self.save_notification(interaction, False)

    @discord.ui.button(label="Custom Interval", emoji="⏱️", style=discord.ButtonStyle.primary, custom_id="custom_interval")
    async def custom_interval_button(self, interaction, button):
        modal = RepeatIntervalModal(self)
        await interaction.response.send_modal(modal)

    async def save_notification(self, interaction, repeat, repeat_minutes=0, interval_text=None):
        try:
            notification_id = await self.cog.save_notification(
                guild_id=interaction.guild_id,
                channel_id=self.channel_id,
                start_date=self.start_date,
                hour=self.hour,
                minute=self.minute,
                timezone=self.timezone,
                description=self.description,
                created_by=interaction.user.id,
                notification_type=self.notification_type,
                mention_type=self.mention_type,
                repeat_48h=repeat,
                repeat_minutes=repeat_minutes
            )

            notification_types = {
                1: "Sends notifications at 30 minutes, 10 minutes, 5 minutes before and when time's up",
                2: "Sends notifications at 10 minutes, 5 minutes before and when time's up",
                3: "Sends notifications at 5 minutes before and when time's up",
                4: "Sends notification only 5 minutes before",
                5: "Sends notification only when time's up",
                6: "Sends notifications at custom times"
            }

            if self.mention_type == "everyone":
                mention_display = "@everyone"
            elif self.mention_type.startswith("role_"):
                role_id = int(self.mention_type.split('_')[1])
                role = interaction.guild.get_role(role_id)
                mention_display = f"@{role.name}" if role else f"Role: {role_id}"
            elif self.mention_type.startswith("member_"):
                member_id = int(self.mention_type.split('_')[1])
                member = interaction.guild.get_member(member_id)
                mention_display = f"@{member.display_name}" if member else f"Member: {member_id}"
            else:
                mention_display = "Unknown"

            if not repeat:
                repeat_text = "❌ No repeat"
            elif interval_text:
                repeat_text = f"🔄 Repeats every {interval_text}"
            else:
                minutes = repeat_minutes
                if minutes == 1:
                    repeat_text = "🔄 Repeats every minute"
                elif minutes == 60:
                    repeat_text = "🔄 Repeats every hour"
                elif minutes == 1440:
                    repeat_text = "🔄 Repeats daily"
                elif minutes == 2880:
                    repeat_text = "🔄 Repeats every 2 days"
                elif minutes == 4320:
                    repeat_text = "🔄 Repeats every 3 days"
                elif minutes == 10080:
                    repeat_text = "🔄 Repeats weekly"
                else:
                    repeat_text = f"🔄 Repeats every {minutes} minutes"

            embed = discord.Embed(
                title="✅ Notification Set Successfully",
                description=(
                    f"**📅 Date:** {self.start_date.strftime('%d/%m/%Y')}\n"
                    f"**⏰ Time:** {self.hour:02d}:{self.minute:02d} {self.timezone}\n"
                    f"**📢 Channel:** <#{self.channel_id}>\n"
                    f"**📝 Description:** {self.description}\n\n"
                    f"**⚙️ Notification Type**\n{notification_types[self.notification_type]}\n\n"
                    f"**👥 Mentions:** {mention_display}\n"
                    f"**🔄 Repeat:** {repeat_text}"
                ),
                color=discord.Color.green()
            )

            embed.set_footer(text="Created at")
            embed.timestamp = datetime.now()
            
            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            print(f"Error saving notification: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while saving the notification.",
                ephemeral=True
            )

class BearTrapView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Set Time",
        emoji="⏰",
        style=discord.ButtonStyle.primary,
        custom_id="set_time",
        row=0
    )
    async def set_time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.check_admin(interaction):
            return
        modal = TimeSelectModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Remove Notification",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="remove_notification",
        row=0
    )
    async def remove_notification_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.check_admin(interaction):
            return
        try:
            notifications = await self.cog.get_notifications(interaction.guild_id)
            if not notifications:
                await interaction.response.send_message(
                    "❌ No notifications found for this server.",
                    ephemeral=True
                )
                return

            options = []
            for notif in notifications:
                display_description = notif[6].split('|')[-1] if '|' in notif[6] else notif[6]
                options.append(
                    discord.SelectOption(
                        label=f"{notif[3]:02d}:{notif[4]:02d} - {display_description[:30]}",
                        description=f"ID: {notif[0]}",
                        value=str(notif[0])
                    )
                )

            select = discord.ui.Select(
                placeholder="Select a notification to remove",
                options=options[:25]
            )

            async def select_callback(select_interaction):
                try:
                    notification_id = int(select_interaction.data["values"][0])
                    selected_notif = next(n for n in notifications if n[0] == notification_id)

                    notification_types = {
                        1: "Sends notifications at 30 minutes, 10 minutes, 5 minutes before and when time's up",
                        2: "Sends notifications at 10 minutes, 5 minutes before and when time's up",
                        3: "Sends notifications at 5 minutes before and when time's up",
                        4: "Sends notification only 5 minutes before",
                        5: "Sends notification only when time's up",
                        6: "Sends notifications at custom times"
                    }

                    mention_type = selected_notif[8]
                    if mention_type == "everyone":
                        mention_display = "@everyone"
                    elif mention_type.startswith("role_"):
                        role_id = int(mention_type.split('_')[1])
                        role = select_interaction.guild.get_role(role_id)
                        mention_display = f"@{role.name}" if role else f"Role: {role_id}"
                    elif mention_type.startswith("member_"):
                        member_id = int(mention_type.split('_')[1])
                        member = select_interaction.guild.get_member(member_id)
                        mention_display = f"@{member.display_name}" if member else f"Member: {member_id}"
                    else:
                        mention_display = "Unknown"

                    if not selected_notif[9]:  
                        repeat_text = "❌ No repeat"
                    else:
                        minutes = selected_notif[10]  
                        if minutes == 1:
                            repeat_text = "🔄 Repeats every minute"
                        elif minutes == 60:
                            repeat_text = "🔄 Repeats every hour"
                        elif minutes == 1440:
                            repeat_text = "🔄 Repeats daily"
                        elif minutes == 2880:
                            repeat_text = "🔄 Repeats every 2 days"
                        elif minutes == 4320:
                            repeat_text = "🔄 Repeats every 3 days"
                        elif minutes == 10080:
                            repeat_text = "🔄 Repeats weekly"
                        else:
                            repeat_text = f"🔄 Repeats every {minutes} minutes"

                    embed = discord.Embed(
                        title="🗑️ Remove Notification",
                        description=(
                            f"**📅 Date:** {datetime.fromisoformat(selected_notif[15]).strftime('%d/%m/%Y')}\n"
                            f"**⏰ Time:** {selected_notif[3]:02d}:{selected_notif[4]:02d} {selected_notif[5]}\n"
                            f"**📢 Channel:** <#{selected_notif[2]}>\n"
                            f"**📝 Description:** {selected_notif[6].split('|')[-1] if '|' in selected_notif[6] else selected_notif[6]}\n\n"
                            f"**⚙️ Notification Type**\n{notification_types[selected_notif[7]]}\n\n"
                            f"**👥 Mentions:** {mention_display}\n"
                            f"**🔄 Repeat:** {repeat_text}\n\n"
                            "Are you sure you want to remove this notification?"
                        ),
                        color=discord.Color.red()
                    )

                    confirm_view = discord.ui.View()
                    
                    async def confirm_callback(confirm_interaction):
                        try:

                            self.cog.cursor.execute("DELETE FROM notification_history WHERE notification_id = ?", (notification_id,))

                            self.cog.cursor.execute("DELETE FROM bear_notifications WHERE id = ?", (notification_id,))
                            
                            self.cog.conn.commit()
                            await confirm_interaction.response.edit_message(
                                content="✅ Notification and its history have been removed successfully.",
                                embed=None,
                                view=None
                            )
                        except Exception as e:
                            print(f"Error removing notification: {e}")
                            await confirm_interaction.response.send_message(
                                "❌ An error occurred while removing the notification.",
                                ephemeral=True
                            )

                    async def cancel_callback(cancel_interaction):
                        await cancel_interaction.response.edit_message(
                            content="❌ Removal cancelled.",
                            embed=None,
                            view=None
                        )

                    confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
                    cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
                    
                    confirm_button.callback = confirm_callback
                    cancel_button.callback = cancel_callback
                    
                    confirm_view.add_item(confirm_button)
                    confirm_view.add_item(cancel_button)
                    
                    await select_interaction.response.edit_message(embed=embed, view=confirm_view)
                except Exception as e:
                    print(f"Error in remove notification callback: {e}")
                    await select_interaction.response.send_message(
                        "❌ An error occurred while removing the notification.",
                        ephemeral=True
                    )

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(
                "Select a notification to remove:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in remove notification: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while loading notifications.",
                ephemeral=True
            )

    @discord.ui.button(
        label="View Notifications",
        emoji="📋",
        style=discord.ButtonStyle.primary,
        custom_id="view_notifications",
        row=1
    )
    async def view_notifications_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.check_admin(interaction):
            return
        try:
            notifications = await self.cog.get_notifications(interaction.guild_id)
            if not notifications:
                await interaction.response.send_message(
                    "❌ No notifications found for this server.",
                    ephemeral=True
                )
                return

            options = []
            for notif in notifications:
                status = "🟢 Enabled" if notif[11] else "🔴 Disabled"
                display_description = notif[6].split('|')[-1] if '|' in notif[6] else notif[6]
                options.append(
                    discord.SelectOption(
                        label=f"{notif[3]:02d}:{notif[4]:02d} - {display_description[:30]}",
                        description=f"ID: {notif[0]} | {status}",
                        value=str(notif[0])
                    )
                )

            select = discord.ui.Select(
                placeholder="Select a notification to view details",
                options=options[:25]
            )

            async def select_callback(select_interaction):
                try:
                    notification_id = int(select_interaction.data["values"][0])
                    selected_notif = next(n for n in notifications if n[0] == notification_id)

                    notification_types = {
                        1: "Sends notifications at 30 minutes, 10 minutes, 5 minutes before and when time's up",
                        2: "Sends notifications at 10 minutes, 5 minutes before and when time's up",
                        3: "Sends notifications at 5 minutes before and when time's up",
                        4: "Sends notification only 5 minutes before",
                        5: "Sends notification only when time's up",
                        6: "Sends notifications at custom times"
                    }

                    mention_type = selected_notif[8]
                    if mention_type == "everyone":
                        mention_display = "@everyone"
                    elif mention_type.startswith("role_"):
                        role_id = int(mention_type.split('_')[1])
                        role = select_interaction.guild.get_role(role_id)
                        mention_display = f"@{role.name}" if role else f"Role: {role_id}"
                    elif mention_type.startswith("member_"):
                        member_id = int(mention_type.split('_')[1])
                        member = select_interaction.guild.get_member(member_id)
                        mention_display = f"@{member.display_name}" if member else f"Member: {member_id}"
                    else:
                        mention_display = "Unknown"

                    if not selected_notif[9]:  
                        repeat_text = "❌ No repeat"
                    else:
                        minutes = selected_notif[10]  
                        if minutes == 1:
                            repeat_text = "🔄 Repeats every minute"
                        elif minutes == 60:
                            repeat_text = "🔄 Repeats every hour"
                        elif minutes == 1440:
                            repeat_text = "🔄 Repeats daily"
                        elif minutes == 2880:
                            repeat_text = "🔄 Repeats every 2 days"
                        elif minutes == 4320:
                            repeat_text = "🔄 Repeats every 3 days"
                        elif minutes == 10080:
                            repeat_text = "🔄 Repeats weekly"
                        else:
                            repeat_text = f"🔄 Repeats every {minutes} minutes"

                    next_notification = datetime.fromisoformat(selected_notif[15])
                    tz = pytz.timezone(selected_notif[5])  
                    
                    if not next_notification.tzinfo:
                        next_notification = tz.localize(next_notification)

                    now = datetime.now(tz)

                    if selected_notif[9] and selected_notif[10] > 0:  

                        custom_times = None
                        if selected_notif[7] == 6 and 'CUSTOM_TIMES:' in selected_notif[6]:
                            custom_times = [int(t) for t in selected_notif[6].split('CUSTOM_TIMES:')[1].split('|')[0].split('-')]

                        self.cog.cursor.execute("""
                            SELECT sent_at, notification_time
                            FROM notification_history 
                            WHERE notification_id = ?
                            ORDER BY sent_at DESC
                            LIMIT 1
                        """, (notification_id,))
                        
                        last_notification_data = self.cog.cursor.fetchone()
                        
                        if last_notification_data and custom_times:
                            last_notification_time, last_custom_time = last_notification_data
                            last_notification = datetime.strptime(last_notification_time, '%Y-%m-%d %H:%M:%S')
                            last_notification = tz.localize(last_notification)

                            time_diff = (now - last_notification).total_seconds() / 60
                            periods_passed = int(time_diff / selected_notif[10])
                            next_base = last_notification + timedelta(minutes=selected_notif[10] * periods_passed)

                            minutes_until_next = (next_base - now).total_seconds() / 60
                            next_custom_time = None

                            sorted_times = sorted(custom_times, reverse=True)
                            for custom_time in sorted_times:
                                if minutes_until_next > custom_time:

                                    if custom_time < last_custom_time:
                                        next_custom_time = custom_time
                                        break
                            
                            if next_custom_time is None:  

                                next_base = next_base + timedelta(minutes=selected_notif[10])
                                next_custom_time = max(custom_times)
                            
                            next_notification = next_base - timedelta(minutes=next_custom_time)
                        elif custom_times:

                            base_time = datetime.fromisoformat(selected_notif[15])
                            if not base_time.tzinfo:
                                base_time = tz.localize(base_time)

                            next_custom_time = max(custom_times)
                            next_notification = base_time - timedelta(minutes=next_custom_time)

                            if next_notification < now:
                                periods_to_add = ((now - next_notification).total_seconds() // 60) // selected_notif[10] + 1
                                next_notification = base_time + timedelta(minutes=selected_notif[10] * periods_to_add) - timedelta(minutes=next_custom_time)
                        else:

                            time_diff = (now - next_notification).total_seconds() / 60
                            periods_passed = int(time_diff / selected_notif[10]) + 1
                            next_notification = next_notification + timedelta(minutes=selected_notif[10] * periods_passed)

                        time_until = next_notification - now

                        days = time_until.days
                        hours, remainder = divmod(time_until.seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        time_parts = []
                        if days > 0:
                            time_parts.append(f"{days} day{'s' if days != 1 else ''}")
                        if hours > 0:
                            time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                        if minutes > 0:
                            time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                        if seconds > 0 or not time_parts:
                            time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
                        
                        time_until_text = ", ".join(time_parts)

                        description = (
                            f"**📅 Date:** {next_notification.strftime('%d/%m/%Y')}\n"
                            f"**⏰ Time:** {selected_notif[3]:02d}:{selected_notif[4]:02d} {selected_notif[5]}\n"
                            f"**📢 Channel:** <#{selected_notif[2]}>\n"
                            f"**📝 Description:** {selected_notif[6].split('|')[-1] if '|' in selected_notif[6] else selected_notif[6]}\n\n"
                            f"**⚙️ Notification Type**\n{notification_types[selected_notif[7]]}\n"
                        )

                        if selected_notif[7] == 6 and 'CUSTOM_TIMES:' in selected_notif[6]:  
                            custom_times = selected_notif[6].split('CUSTOM_TIMES:')[1].split('|')[0].split('-')
                            description += f"**🕒 Custom Times:** {', '.join(custom_times)} minutes before\n"

                        description += (
                            f"\n**👥 Mentions:** {mention_display}\n"
                            f"**🔄 Repeat:** {repeat_text}\n\n"
                            f"**⏳ Next notification in:** {time_until_text}"
                        )

                        embed = discord.Embed(
                            title="📋 Notification Details",
                            description=description,
                            color=discord.Color.blue()
                        )
                        
                        await select_interaction.response.edit_message(embed=embed)
                        
                except Exception as e:
                    print(f"Error in view notification callback: {e}")
                    import traceback
                    traceback.print_exc()
                    await select_interaction.response.send_message(
                        "❌ An error occurred while viewing notification details.",
                        ephemeral=True
                    )

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(
                "Select a notification to view details:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error viewing notifications: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while loading notifications.",
                ephemeral=True
            )

    @discord.ui.button(
        label="Enable/Disable",
        emoji="✅",
        style=discord.ButtonStyle.primary,
        custom_id="toggle_notifications",
        row=1
    )
    async def toggle_notifications_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.check_admin(interaction):
            return
        try:
            notifications = await self.cog.get_notifications(interaction.guild_id)
            if not notifications:
                await interaction.response.send_message(
                    "❌ No notifications found for this server.",
                    ephemeral=True
                )
                return

            options = []
            for notif in notifications:
                status = "🟢 Enabled" if notif[11] else "🔴 Disabled"
                display_description = notif[6].split('|')[-1] if '|' in notif[6] else notif[6]
                options.append(
                    discord.SelectOption(
                        label=f"{notif[3]:02d}:{notif[4]:02d} - {display_description[:30]}",
                        description=f"ID: {notif[0]} | {status}",
                        value=str(notif[0])
                    )
                )

            select = discord.ui.Select(
                placeholder="Select a notification to toggle",
                options=options[:25]
            )

            async def select_callback(select_interaction):
                notification_id = int(select_interaction.data["values"][0])
                current_status = next(n[11] for n in notifications if n[0] == notification_id)
                new_status = not current_status
                
                if await self.cog.toggle_notification(notification_id, new_status):
                    status_text = "enabled" if new_status else "disabled"
                    embed = discord.Embed(
                        title="✅ Notification Status Updated",
                        description=f"The notification has been {status_text}.",
                        color=discord.Color.green() if new_status else discord.Color.red()
                    )
                    await select_interaction.response.edit_message(embed=embed, view=None)
                else:
                    await select_interaction.response.send_message(
                        "❌ Failed to update notification status.",
                        ephemeral=True
                    )

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(
                "Select a notification to toggle:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in toggle notifications: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while loading notifications.",
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
        if not await self.cog.check_admin(interaction):
            return
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

class RepeatIntervalModal(discord.ui.Modal, title="Set Repeat Interval"):
    def __init__(self, repeat_view: RepeatOptionView):
        super().__init__()
        self.repeat_view = repeat_view
        
        self.months = discord.ui.TextInput(
            label="Months",
            placeholder="Enter number of months (e.g., 1)",
            min_length=0,
            max_length=2,
            required=False,
            default="0"
        )
        self.add_item(self.months)
        
        self.weeks = discord.ui.TextInput(
            label="Weeks",
            placeholder="Enter number of weeks (e.g., 2)",
            min_length=0,
            max_length=2,
            required=False,
            default="0"
        )
        self.add_item(self.weeks)
        
        self.days = discord.ui.TextInput(
            label="Days",
            placeholder="Enter number of days (e.g., 3)",
            min_length=0,
            max_length=2,
            required=False,
            default="0"
        )
        self.add_item(self.days)
        
        self.hours = discord.ui.TextInput(
            label="Hours",
            placeholder="Enter number of hours (e.g., 12)",
            min_length=0,
            max_length=2,
            required=False,
            default="0"
        )
        self.add_item(self.hours)
        
        self.minutes = discord.ui.TextInput(
            label="Minutes",
            placeholder="Enter number of minutes (e.g., 30)",
            min_length=0,
            max_length=2,
            required=False,
            default="0"
        )
        self.add_item(self.minutes)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            try:
                months = int(self.months.value)
                weeks = int(self.weeks.value)
                days = int(self.days.value)
                hours = int(self.hours.value)
                minutes = int(self.minutes.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Please enter valid numbers for all fields!",
                    ephemeral=True
                )
                return

            if not any([months > 0, weeks > 0, days > 0, hours > 0, minutes > 0]):
                await interaction.response.send_message(
                    "❌ Please enter at least one time interval greater than 0!",
                    ephemeral=True
                )
                return

            total_minutes = (months * 30 * 24 * 60) + (weeks * 7 * 24 * 60) + (days * 24 * 60) + (hours * 60) + minutes

            interval_parts = []
            if months > 0:
                interval_parts.append(f"{months} month{'s' if months > 1 else ''}")
            if weeks > 0:
                interval_parts.append(f"{weeks} week{'s' if weeks > 1 else ''}")
            if days > 0:
                interval_parts.append(f"{days} day{'s' if days > 1 else ''}")
            if hours > 0:
                interval_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                interval_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            
            if len(interval_parts) > 1:
                interval_text = ", ".join(interval_parts[:-1]) + " and " + interval_parts[-1]
            else:
                interval_text = interval_parts[0]
            
            await self.repeat_view.save_notification(interaction, True, total_minutes, interval_text)

        except Exception as e:
            print(f"Error in repeat interval modal: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting the repeat interval.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(BearTrap(bot)) 