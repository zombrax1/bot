"""
Core bot operations. Admin management, alliance control messages, and bot settings.
"""
import discord
from discord.ext import commands
import os
import re
import sys
import sqlite3
import asyncio
import requests
import logging
import subprocess
from .permission_handler import PermissionManager
from .pimp_my_bot import theme, safe_edit_message

logger = logging.getLogger('bot')


ORIGIN_URL = "https://github.com/zombrax1/bot.git"
UPSTREAM_URL = "https://github.com/whiteout-project/bot.git"


class _UpdateChoiceView(discord.ui.View):
    """Global-admin update source picker. Each choice has a confirmation step."""

    def __init__(self, bot):
        super().__init__(timeout=7200)
        self.bot = bot

    async def _confirm(self, interaction: discord.Interaction, source: str):
        is_admin, is_global = PermissionManager.is_admin(interaction.user.id)
        if not is_admin or not is_global:
            await interaction.response.send_message(
                f"{theme.deniedIcon} Only Global Admins can update the bot.",
                ephemeral=True,
            )
            return
        label = "ZomBrox Update" if source == "origin" else "Upstream Update"
        remote = ORIGIN_URL if source == "origin" else UPSTREAM_URL
        description = (
            "Fetches your fork and applies it only when it can fast-forward the current branch."
            if source == "origin" else
            "Fetches the original project and safely merges it into the current branch. "
            "Conflicts are aborted; nothing is overwritten or pushed."
        )
        embed = discord.Embed(
            title=f"{theme.warnIcon} Confirm {label}",
            description=f"{description}\n\n**Source:** `{remote}`\n\nContinue with this update?",
            color=discord.Color.orange(),
        )
        await interaction.response.edit_message(embed=embed, view=_UpdateConfirmView(self.bot, source))

    @discord.ui.button(label="ZomBrox Update", emoji=f"{theme.refreshIcon}",
                       style=discord.ButtonStyle.primary)
    async def origin_update(self, interaction, button):
        await self._confirm(interaction, "origin")

    @discord.ui.button(label="Upstream Update", emoji=f"{theme.refreshIcon}",
                       style=discord.ButtonStyle.secondary)
    async def upstream_update(self, interaction, button):
        await self._confirm(interaction, "upstream")


class _UpdateConfirmView(discord.ui.View):
    def __init__(self, bot, source: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.source = source

    @discord.ui.button(label="Confirm Update", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin, is_global = PermissionManager.is_admin(interaction.user.id)
        if not is_admin or not is_global:
            await interaction.response.send_message(
                f"{theme.deniedIcon} Only Global Admins can update the bot.", ephemeral=True)
            return
        button.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(title=f"{theme.refreshIcon} Updating Bot",
                description="Checking the worktree and fetching the selected source...",
                color=discord.Color.yellow()), view=self)
        cog = self.bot.get_cog("BotOperations")
        result = await cog.perform_git_update(self.source)
        color = (discord.Color.green() if result["ok"] else
                 discord.Color.blue() if result["unchanged"] else discord.Color.red())
        embed = discord.Embed(title=result["title"], description=result["message"], color=color)
        embed.add_field(name="Changes", value="Yes" if result["changed"] else "No", inline=True)
        embed.add_field(name="Update Result", value=result["status"], inline=True)
        embed.add_field(name="Restart Required", value="Yes" if result["changed"] else "No", inline=True)
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="Update Cancelled",
                description="No repository changes were made.", color=discord.Color.greyple()), view=None)


class BotOperations(commands.Cog):
    def __init__(self, bot, conn):
        self.bot = bot
        self.conn = conn
        self.settings_db = sqlite3.connect('db/settings.sqlite', timeout=30.0, check_same_thread=False)
        self.settings_cursor = self.settings_db.cursor()
        self.alliance_db = sqlite3.connect('db/alliance.sqlite', timeout=30.0, check_same_thread=False)
        self.c_alliance = self.alliance_db.cursor()
        self.setup_database()

    def get_current_version(self):
        """Get current version from version file"""
        try:
            if os.path.exists("version"):
                with open("version", "r") as f:
                    return f.read().strip()
            return "v0.0.0"
        except Exception:
            return "v0.0.0"

    @staticmethod
    def _git(*args):
        """Run git without a shell so Discord input can never become a command."""
        return subprocess.run(
            ["git", *args], cwd=os.path.abspath(os.curdir), text=True,
            capture_output=True, timeout=120, check=False,
        )

    def _perform_git_update_sync(self, source: str) -> dict:
        result = {"ok": False, "unchanged": False, "changed": False,
                  "title": "Update Blocked", "status": "Not run", "message": ""}
        if source not in {"origin", "upstream"}:
            result["message"] = "Unknown update source. No changes were made."
            return result

        expected_url = ORIGIN_URL if source == "origin" else UPSTREAM_URL
        actual = self._git("remote", "get-url", source)
        if actual.returncode or actual.stdout.strip().rstrip("/") != expected_url.rstrip("/"):
            result["message"] = (
                f"The `{source}` remote is missing or does not match `{expected_url}`. "
                "Remote roles were not changed and no update was attempted."
            )
            return result

        # Tracked edits or an unfinished Git operation make an automatic update unsafe.
        dirty = self._git("status", "--porcelain", "--untracked-files=no")
        git_dir = self._git("rev-parse", "--git-dir")
        if dirty.returncode or dirty.stdout.strip() or git_dir.returncode:
            result["message"] = (
                "The checkout has tracked local changes or Git could not inspect it. "
                "Nothing was fetched, merged, reset, or discarded."
            )
            return result
        git_path = os.path.abspath(git_dir.stdout.strip())
        if any(os.path.exists(os.path.join(git_path, marker)) for marker in
               ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply")):
            result["message"] = "A Git merge/rebase operation is already in progress. Nothing was changed."
            return result

        branch = self._git("branch", "--show-current")
        if branch.returncode or not branch.stdout.strip():
            result["message"] = "The checkout is not on a branch. Nothing was changed."
            return result
        branch_name = branch.stdout.strip()
        before = self._git("rev-parse", "HEAD")
        fetched = self._git("fetch", "--prune", source)
        if fetched.returncode:
            result.update(title="Update Failed", status="Fetch failed",
                          message=f"Git could not fetch `{source}`. No files were changed.\n```\n{(fetched.stderr or fetched.stdout)[-700:]}\n```")
            return result

        if source == "origin":
            target = f"origin/{branch_name}"
            target_check = self._git("rev-parse", "--verify", target)
            if target_check.returncode:
                result.update(title="Update Failed", status="Branch not found",
                              message=f"`{target}` does not exist. No files were changed.")
                return result
            merge = self._git("merge", "--ff-only", target)
        else:
            target = "upstream/main"
            target_check = self._git("rev-parse", "--verify", target)
            if target_check.returncode:
                result.update(title="Update Failed", status="Branch not found",
                              message=f"`{target}` does not exist. No files were changed.")
                return result
            merge = self._git("merge", "--no-edit", target)

        if merge.returncode:
            # A conflicting upstream merge is always returned to its exact pre-update state.
            if os.path.exists(os.path.join(git_path, "MERGE_HEAD")):
                self._git("merge", "--abort")
            result.update(title="Update Failed", status="Merge not applied",
                          message=("The update could not be integrated safely. Any attempted merge "
                                   "was aborted; local files and untracked runtime data were preserved.\n"
                                   f"```\n{(merge.stderr or merge.stdout)[-650:]}\n```"))
            return result

        after = self._git("rev-parse", "HEAD")
        changed = before.stdout.strip() != after.stdout.strip()
        if not changed:
            result.update(unchanged=True, title="Already Up to Date", status="No changes",
                          message=f"`{target}` has no new changes for this checkout. No restart is required.")
        else:
            result.update(ok=True, changed=True, title="Update Successful", status="Merge succeeded",
                          message=(f"Changes from `{target}` were integrated successfully. "
                                   "Restart the bot to run the updated code. No remote was pushed."))
        return result

    async def perform_git_update(self, source: str) -> dict:
        return await asyncio.to_thread(self._perform_git_update_sync, source)
        
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

            # Migration: add is_owner column for the explicit Bot Owner anchor.
            # is_owner=1 means THE bot owner (recovery anchor, can't be removed
            # except via explicit Transfer Owner). is_initial=1 means Global
            # tier (multiple allowed). is_owner always implies is_initial.
            self.settings_cursor.execute("PRAGMA table_info(admin)")
            admin_cols = [row[1] for row in self.settings_cursor.fetchall()]
            if 'is_owner' not in admin_cols:
                self.settings_cursor.execute(
                    "ALTER TABLE admin ADD COLUMN is_owner INTEGER DEFAULT 0"
                )

            # Single-row table storing the bot's Discord activity status.
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_presence (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    activity_type TEXT NOT NULL DEFAULT 'playing',
                    activity_text TEXT NOT NULL DEFAULT 'Whiteout Survival',
                    activity_url TEXT
                )
            """)
            self.settings_cursor.execute(
                "INSERT OR IGNORE INTO bot_presence (id) VALUES (1)"
            )

            self.settings_db.commit()
            self._backfill_owner_if_needed()

        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            print(f"Error setting up database: {e}")

    def _backfill_owner_if_needed(self):
        """One-shot owner backfill on startup.

        - If any admin already has is_owner=1: no-op (idempotent).
        - If exactly one admin has is_initial=1: promote that admin to owner.
        - Otherwise (0 or >=2 globals, no owner yet): leave unset, log a
          console banner so the actual host knows to claim ownership the
          first time they open Settings → Permissions.
        """
        self.settings_cursor.execute("SELECT 1 FROM admin WHERE is_owner = 1 LIMIT 1")
        if self.settings_cursor.fetchone():
            return

        self.settings_cursor.execute("SELECT id FROM admin WHERE is_initial = 1")
        globals_ = [row[0] for row in self.settings_cursor.fetchall()]

        if len(globals_) == 1:
            self.settings_cursor.execute(
                "UPDATE admin SET is_owner = 1 WHERE id = ?", (globals_[0],)
            )
            self.settings_db.commit()
            logger.info(f"[OWNER-CLAIM] Auto-promoted single Global admin {globals_[0]} to Bot Owner.")
        elif len(globals_) >= 2:
            msg = (
                f"[OWNER-CLAIM] {len(globals_)} Global admins detected, no Bot Owner is set. "
                f"The first Global admin to open Settings -> Permissions and click 'Claim Bot Owner' "
                f"becomes the permanent owner."
            )
            logger.warning(msg)
        # len(globals_) == 0: brand-new install. The first admin created via
        # the new Add Admin flow gets is_initial=1, is_owner=1 atomically.

    async def cog_unload(self):
        """Close database connections when cog is unloaded."""
        try:
            self.settings_db.close()
            self.alliance_db.close()
            if hasattr(self, 'conn'):
                self.conn.close()
        except Exception:
            pass

    # ── Bot Presence (activity status) ──────────────────────────────────

    def get_bot_presence(self) -> dict:
        """Read the persisted bot presence settings."""
        self.settings_cursor.execute(
            "SELECT activity_type, activity_text, activity_url FROM bot_presence WHERE id = 1"
        )
        row = self.settings_cursor.fetchone()
        if not row:
            return {'activity_type': 'playing', 'activity_text': 'Whiteout Survival', 'activity_url': None}
        return {'activity_type': row[0], 'activity_text': row[1], 'activity_url': row[2]}

    async def set_bot_presence(self, *, activity_type: str = None,
                                activity_text: str = None,
                                activity_url: str = None) -> None:
        """Persist + apply a presence change. Pass only the fields you want to
        update; the rest stay at their current values."""
        current = self.get_bot_presence()
        new_type = activity_type if activity_type is not None else current['activity_type']
        new_text = activity_text if activity_text is not None else current['activity_text']
        new_url = activity_url if activity_url is not None else current['activity_url']

        self.settings_cursor.execute(
            "UPDATE bot_presence SET activity_type = ?, activity_text = ?, activity_url = ? WHERE id = 1",
            (new_type, new_text, new_url),
        )
        self.settings_db.commit()
        await self._apply_presence(new_type, new_text, new_url)

    async def _apply_presence(self, activity_type: str, activity_text: str,
                              activity_url: str | None) -> None:
        """Push the given presence to Discord via change_presence."""
        try:
            if activity_type == 'custom':
                # Custom status shows the text alone, with no "Playing/Watching" verb.
                activity = discord.CustomActivity(name=activity_text)
            elif activity_type == 'streaming' and activity_url:
                activity = discord.Streaming(name=activity_text, url=activity_url)
            else:
                # Streaming-without-URL silently falls back to Playing
                # (Discord would drop it anyway without a valid URL).
                lookup = 'playing' if activity_type == 'streaming' else activity_type
                api_type = getattr(discord.ActivityType, lookup, discord.ActivityType.playing)
                activity = discord.Activity(type=api_type, name=activity_text)
            await self.bot.change_presence(activity=activity)
        except Exception as e:
            logger.warning(f"Failed to apply bot presence: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Apply the persisted presence after the bot connects."""
        p = self.get_bot_presence()
        await self._apply_presence(p['activity_type'], p['activity_text'], p['activity_url'])

    async def show_bot_presence(self, interaction: discord.Interaction):
        """Open the Bot Presence settings view. Global Admin only."""
        try:
            _, is_global = PermissionManager.is_admin(interaction.user.id)
            if not is_global:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} Only Global Admins can change the bot's presence.",
                    ephemeral=True,
                )
                return
            view = BotPresenceView(self)
            await safe_edit_message(interaction, embed=view.build_embed(), view=view, content=None)
        except Exception as e:
            logger.error(f"Error showing bot presence: {e}")
            print(f"Error showing bot presence: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.warnIcon} Couldn't open Bot Presence settings. Please try again.",
                    ephemeral=True,
                )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        
        if custom_id == "bot_operations":
            return
        
        if custom_id == "alliance_control_messages":
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.warnIcon} The bot-wide toggle was replaced by a per-alliance "
                    f"\"Show Sync Messages\" setting under the alliance's Settings.",
                    ephemeral=True,
                )
            return

        if custom_id in (
            "assign_alliance", "add_admin", "remove_admin",
            "view_admin_permissions", "view_administrators",
        ):
            # The old Permissions UI was rebuilt as a single admin-list flow
            # (see show_permissions in bot_main_menu.py). These custom_ids
            # only fire from stale persisted messages — point users at the
            # new flow instead of erroring.
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.warnIcon} The Permissions menu was redesigned. "
                    f"Please reopen Settings → Permissions to use the new flow.",
                    ephemeral=True,
                )
            return

        elif custom_id in ["main_menu", "bot_status", "bot_settings"]:
            try:
                if custom_id == "main_menu":
                    try:
                        main_menu_cog = self.bot.get_cog("MainMenu")
                        if main_menu_cog:
                            await main_menu_cog.show_main_menu(interaction)
                        else:
                            await interaction.response.send_message(
                                f"{theme.deniedIcon} An error occurred while returning to main menu.",
                                ephemeral=True
                            )
                    except Exception as e:
                        logger.error(f"Main Menu error in bot operations: {e}")
                        print(f"[ERROR] Main Menu error in bot operations: {e}")
                        if not interaction.response.is_done():
                            await interaction.response.send_message(
                                "An error occurred while returning to main menu.",
                                ephemeral=True
                            )
                        else:
                            await interaction.followup.send(
                                "An error occurred while returning to main menu.",
                                ephemeral=True
                            )

            except Exception as e:
                if not interaction.response.is_done():
                    logger.error(f"Error processing {custom_id}: {e}")
                    print(f"Error processing {custom_id}: {e}")
                    await interaction.response.send_message(
                        "An error occurred while processing your request.",
                        ephemeral=True
                    )
        elif custom_id == "check_updates":
            try:
                is_admin, is_global = PermissionManager.is_admin(interaction.user.id)

                if not is_admin or not is_global:
                    await interaction.response.send_message(
                        f"{theme.deniedIcon} Only global administrators can use this command.",
                        ephemeral=True
                    )
                    return

                main_embed = discord.Embed(
                    title=f"{theme.refreshIcon} Check for Updates",
                    description=(
                        "Choose which trusted source to check. You will be asked to confirm "
                        "before Git fetches or integrates anything.\n\n"
                        "**ZomBrox Update**\nUpdates this checkout from your fork "
                        f"(`{ORIGIN_URL}`). It only applies a safe fast-forward.\n\n"
                        "**Upstream Update**\nFetches the original project "
                        f"(`{UPSTREAM_URL}`) and safely merges it into this checkout. "
                        "Conflicts are aborted; it never overwrites with a reset."
                    ),
                    color=theme.emColor1,
                )
                main_embed.add_field(
                    name="Safety",
                    value=("Tracked local edits or an unfinished Git operation block the update. "
                           "Untracked runtime data is preserved. Nothing is pushed to either remote."),
                    inline=False,
                )
                await interaction.response.send_message(
                    embed=main_embed,
                    view=_UpdateChoiceView(self.bot),
                    ephemeral=True,
                )

            except Exception as e:
                logger.error(f"Check updates error: {e}")
                print(f"Check updates error: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"{theme.deniedIcon} An error occurred while checking for updates.",
                        ephemeral=True
                    )

    @staticmethod
    def _is_stable_upgrade(current_version: str, latest_tag: str) -> bool:
        """True if latest_tag is a strictly newer vX.Y.Z. Unparseable current
        (e.g. v0.0.0 fresh install) => any differing tag upgrades (pull-forward)."""
        def parse(tag):
            try:
                parts = [int(n) for n in tag.strip().lstrip("vV").split(".")[:3]]
            except (ValueError, AttributeError):
                return None
            if not parts:
                return None
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts)

        cur, latest = parse(current_version), parse(latest_tag)
        if cur is None or latest is None:
            return current_version != latest_tag
        return latest > cur

    async def check_for_updates(self):
        """Check for updates using GitHub releases API"""
        try:
            current_version = self.get_current_version()

            # Beta builds (version "beta-<sha>") track main and are ahead of the
            # latest stable tag, so don't offer the stable release as an update.
            if current_version.startswith("beta-"):
                return current_version, current_version, [], False

            latest_release_url = "https://api.github.com/repos/whiteout-project/bot/releases/latest"

            response = await asyncio.to_thread(requests.get, latest_release_url, timeout=10)
            if response.status_code != 200:
                return None, None, [], False

            latest_release_data = response.json()
            latest_tag = latest_release_data.get("tag_name", "")

            if not latest_tag:
                return current_version, None, [], False

            updates_needed = self._is_stable_upgrade(current_version, latest_tag)
            
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
            logger.error(f"Error checking for updates: {e}")
            print(f"Error checking for updates: {e}")
            return None, None, [], False

# ────────────────────────────────────────────────────────────────────────
# Bot Presence (activity status) views
# ────────────────────────────────────────────────────────────────────────

# (code, label-shown-in-embed, dropdown-emoji). Discord rejects Custom
# activity type for bots; Streaming needs a valid Twitch/YouTube URL.
_PRESENCE_TYPES: list[tuple[str, str, str]] = [
    ('playing',   'Playing',      '🎮'),
    ('streaming', 'Streaming',    '🔴'),
    ('listening', 'Listening to', '🎧'),
    ('watching',  'Watching',     '👁️'),
    ('competing', 'Competing in', '🏆'),
    ('custom',    'Custom',       '💬'),
]
_PRESENCE_VERB = {code: label for code, label, _ in _PRESENCE_TYPES}

_STREAM_URL_RE = re.compile(
    r'^https?://(?:www\.)?(?:twitch\.tv|youtube\.com)/.+',
    re.IGNORECASE,
)


class BotPresenceView(discord.ui.View):
    """Lets a Global admin pick the bot's activity type + edit its text/URL."""

    def __init__(self, cog: 'BotOperations'):
        super().__init__(timeout=7200)
        self.cog = cog
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        _, is_global = PermissionManager.is_admin(interaction.user.id)
        if not is_global:
            await interaction.response.send_message(
                f"{theme.deniedIcon} Only global admins can change bot presence.",
                ephemeral=True,
            )
            return False
        return True

    def build_embed(self) -> discord.Embed:
        p = self.cog.get_bot_presence()
        if p['activity_type'] == 'custom':
            current = f"**{p['activity_text']}**"
        else:
            verb = _PRESENCE_VERB.get(p['activity_type'], 'Playing')
            current = f"{verb} **{p['activity_text']}**"
            if p['activity_type'] == 'streaming' and p['activity_url']:
                current += f"\n└ {p['activity_url']}"
        return discord.Embed(
            title=f"{theme.robotIcon} Bot Presence",
            description=(
                f"Set the activity status shown next to the bot's name in "
                f"Discord. Picking a type from the dropdown applies immediately.\n\n"
                f"{theme.upperDivider}\n"
                f"**Currently:** {current}\n"
                f"{theme.lowerDivider}\n"
                f"_Streaming requires a valid Twitch or YouTube URL — without "
                f"it, Discord shows the activity as Playing._"
            ),
            color=theme.emColor1,
        )

    def _build_components(self):
        self.clear_items()
        current_type = self.cog.get_bot_presence()['activity_type']

        select = discord.ui.Select(
            placeholder="Activity type",
            options=[
                discord.SelectOption(
                    label=label, value=code, emoji=emoji,
                    default=(code == current_type),
                )
                for code, label, emoji in _PRESENCE_TYPES
            ],
            row=0,
        )
        select.callback = self._on_type_change
        self.add_item(select)

        edit_btn = discord.ui.Button(
            label="Edit Text" + (" / URL" if current_type == 'streaming' else ''),
            emoji=theme.editListIcon,
            style=discord.ButtonStyle.primary, row=1,
        )
        edit_btn.callback = self._open_text_modal
        self.add_item(edit_btn)

        back_btn = discord.ui.Button(
            label="Back", emoji=theme.backIcon,
            style=discord.ButtonStyle.secondary, row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _refresh(self, interaction: discord.Interaction):
        self._build_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_type_change(self, interaction: discord.Interaction):
        new_type = interaction.data['values'][0]
        await self.cog.set_bot_presence(activity_type=new_type)
        await self._refresh(interaction)

    async def _open_text_modal(self, interaction: discord.Interaction):
        p = self.cog.get_bot_presence()
        modal = BotPresenceTextModal(
            self, current_text=p['activity_text'],
            current_url=p['activity_url'] or '',
            is_streaming=(p['activity_type'] == 'streaming'),
        )
        await interaction.response.send_modal(modal)

    async def _on_back(self, interaction: discord.Interaction):
        main_menu = self.cog.bot.get_cog("MainMenu")
        if main_menu:
            await main_menu.show_maintenance(interaction)


class BotPresenceTextModal(discord.ui.Modal):
    """Text (and URL when streaming) editor for the bot's activity status."""

    def __init__(self, parent_view: BotPresenceView, *,
                 current_text: str, current_url: str, is_streaming: bool):
        super().__init__(title="Edit Bot Presence")
        self.parent_view = parent_view
        self.is_streaming = is_streaming

        self.text_input = discord.ui.TextInput(
            label="Activity text",
            placeholder="e.g. Whiteout Survival",
            default=current_text, required=True,
            min_length=1, max_length=128,
        )
        self.add_item(self.text_input)

        if is_streaming:
            self.url_input = discord.ui.TextInput(
                label="Stream URL (Twitch or YouTube)",
                placeholder="https://twitch.tv/yourchannel",
                default=current_url, required=True,
                max_length=512,
            )
            self.add_item(self.url_input)
        else:
            self.url_input = None

    async def on_submit(self, interaction: discord.Interaction):
        text = self.text_input.value.strip()
        url = self.url_input.value.strip() if self.url_input else None

        if self.is_streaming:
            if not _STREAM_URL_RE.match(url or ''):
                await interaction.response.send_message(
                    f"{theme.deniedIcon} Stream URL must be a Twitch or YouTube link "
                    f"(e.g. `https://twitch.tv/yourchannel`).",
                    ephemeral=True,
                )
                return

        await self.parent_view.cog.set_bot_presence(activity_text=text, activity_url=url)
        self.parent_view._build_components()
        await interaction.response.edit_message(
            embed=self.parent_view.build_embed(), view=self.parent_view
        )


async def setup(bot):
    await bot.add_cog(BotOperations(bot, sqlite3.connect('db/settings.sqlite')))
