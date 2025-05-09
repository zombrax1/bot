from colorama import Fore, Style, init
import subprocess
import warnings
import shutil
import sys
import os

print("Removing unneccesary files...")

v1_path = "V1oldbot"
if os.path.exists(v1_path) and os.path.isdir(v1_path):
    try:
        shutil.rmtree(v1_path)
        print(f"Removed directory: {v1_path}")
    except PermissionError:
        print(f"Warning: Access Denied. Could not remove legacy directory '{v1_path}'. Please check permissions or if files are in use, then remove manually if needed.")
    except OSError as e:
        print(f"Warning: Could not remove legacy directory '{v1_path}': {e}")

v2_path = "V2Old"
if os.path.exists(v2_path) and os.path.isdir(v2_path):
    try:
        shutil.rmtree(v2_path)
        print(f"Removed directory: {v2_path}")
    except PermissionError:
        print(f"Warning: Access Denied. Could not remove legacy directory '{v2_path}'. Please check permissions or if files are in use, then remove manually if needed.")
    except OSError as e:
        print(f"Warning: Could not remove legacy directory '{v2_path}': {e}")

txt_path = "autoupdateinfo.txt"
if os.path.exists(txt_path) and os.path.isfile(txt_path): 
    try:
        os.remove(txt_path)
        print(f"Removed file: {txt_path}")
    except PermissionError:
        print(f"Warning: Access Denied. Could not remove legacy file '{txt_path}'. Please check permissions or if the file is in use, then remove it manually if needed.")
    except OSError as e:
        print(f"Warning: Could not remove legacy file '{txt_path}': {e}")

print("Cleanup attempt finished.")

warnings.filterwarnings("ignore", category=DeprecationWarning)

init(autoreset=True)

try:
    import ssl
    import certifi

    def _create_ssl_context_with_certifi():
        return ssl.create_default_context(cafile=certifi.where())
    
    original_create_default_https_context = getattr(ssl, "_create_default_https_context", None)

    if original_create_default_https_context is None or \
       original_create_default_https_context is ssl.create_default_context:
        ssl._create_default_https_context = _create_ssl_context_with_certifi
        
        print(Fore.GREEN + "Applied SSL context patch using certifi for default HTTPS connections." + Style.RESET_ALL)
    else: # Assume if it's already patched, it's for a good reason, just log it.
        print(Fore.YELLOW + "SSL default HTTPS context seems to be already modified. Skipping certifi patch." + Style.RESET_ALL)
except ImportError:
    print(Fore.RED + "Certifi library not found. SSL certificate verification might fail until it's installed." + Style.RESET_ALL)
except Exception as e:
    print(Fore.RED + f"Error applying SSL context patch: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    import requests

    def restart_bot():
        print(Fore.YELLOW + "\nRestarting bot..." + Style.RESET_ALL)
        python = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        args = [python, script_path] + sys.argv[1:]

        try: # Try subprocess.Popen first to avoid issues with blank space in the path on Windows
            subprocess.Popen(args)
            os._exit(0)
        except Exception as e:
            print(f"Error restarting: {e}")
            os.execl(python, python, script_path, *sys.argv[1:])
        
    def install_packages(requirements_txt_path: str) -> bool:
        full_command= [sys.executable, "-m", "pip", "install", "-r", requirements_txt_path, "--no-cache-dir", "--ignore-requires-python"]
        
        try:
            subprocess.check_call(full_command, timeout=1200, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as _:
            return False

    async def check_and_update_files():
        latest_release_url = "https://api.github.com/repos/whiteout-project/bot/releases/latest"
        
        latest_release_resp = requests.get(latest_release_url)
        
        if latest_release_resp.status_code == 200:
            latest_release_data = latest_release_resp.json()
            latest_tag = latest_release_data["tag_name"]
            
            if os.path.exists("version"):
                with open("version", "r") as f:
                    current_version = f.read().strip()
            else:
                current_version = "v0.0.0"
                        
            if current_version != latest_tag:
                print(Fore.YELLOW + f"New version available: {latest_tag}" + Style.RESET_ALL)
                print("Update Notes:")
                print(latest_release_data["body"])
                print()
                
                update = False
                
                if any([sys.argv[i]== "--autoupdate" for i in range(len(sys.argv))]):
                    update = True
                else:
                    print("Note: If your terminal is not interactive, you can use the --autoupdate argument to skip this prompt.")
                    ask = input("Do you want to update? (y/n): ").strip().lower()
                    update = ask == "y"
                    
                if update:
                    if os.path.exists("db") and os.path.isdir("db"):
                        print(Fore.YELLOW + "Making backup of database..." + Style.RESET_ALL)
                        
                        if os.path.exists("db.bak") and os.path.isdir("db.bak"):
                            try:
                                shutil.rmtree("db.bak")
                            except PermissionError:
                                print(Fore.RED + "WARNING: db.bak folder could not be removed. A backup will not be created." + Style.RESET_ALL)
                        
                        if not os.path.exists("db.bak"):
                            shutil.copytree("db", "db.bak")
                        
                        print(Fore.GREEN + "Backup completed." + Style.RESET_ALL)
                    
                    download_url = latest_release_data["assets"][0]["browser_download_url"]
                    download_resp = requests.get(download_url)
                    
                    if download_resp.status_code == 200:
                        with open("package.zip", "wb") as f:
                            f.write(download_resp.content)
                        
                        shutil.unpack_archive("package.zip", "update", "zip")
                        
                        os.remove("package.zip")
                        
                        if os.path.exists("update/main.py"):
                            os.rename("update/main.py", "main.py.new")
                            os.rename("main.py", "main.py.bak")
                            os.rename("main.py.new", "main.py")
                            
                        if os.path.exists("update/requirements.txt"):                                
                            print(Fore.YELLOW + "Installing new requirements..." + Style.RESET_ALL)
                            
                            install_packages("update/requirements.txt")
                            os.remove("update/requirements.txt")
                            
                            print(Fore.GREEN + "Requirements installed." + Style.RESET_ALL)
                            
                        for root, _, files in os.walk("update"):
                            for file in files:
                                rel_path = os.path.relpath(os.path.join(root, file), "update")
                                dst_path = os.path.join(".", rel_path)
                                
                                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                                shutil.copy2(os.path.join(root, file), dst_path)
                                
                        shutil.rmtree("update")
                        
                        print(Fore.GREEN + "Update completed successfully. Restarting bot..." + Style.RESET_ALL)
                        
                        with open("version", "w") as f:
                            f.write(latest_tag)
                        
                        restart_bot()
                    else:
                        print(Fore.RED + "Failed to download the update." + Style.RESET_ALL)
                        return  
        else:
            print(Fore.RED + "Failed to fetch latest release info." + Style.RESET_ALL)
            
    import discord
    from discord.ext import commands
    import sqlite3
    import asyncio

    class CustomBot(commands.Bot):
        async def on_error(self, event_name, *args, **kwargs):
            if event_name == "on_interaction":
                error = sys.exc_info()[1]
                if isinstance(error, discord.NotFound) and error.code == 10062:
                    return
            
            await super().on_error(event_name, *args, **kwargs)

        async def on_command_error(self, ctx, error):
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
            await super().on_command_error(ctx, error)

    intents = discord.Intents.default()
    intents.message_content = True

    bot = CustomBot(command_prefix="/", intents=intents)

    init(autoreset=True)

    token_file = "bot_token.txt"
    if not os.path.exists(token_file):
        bot_token = input("Enter the bot token: ")
        with open(token_file, "w") as f:
            f.write(bot_token)
    else:
        with open(token_file, "r") as f:
            bot_token = f.read().strip()

    if not os.path.exists("db"):
        os.makedirs("db")
        
        print(Fore.GREEN + "db folder created" + Style.RESET_ALL)

    databases = {
        "conn_alliance": "db/alliance.sqlite",
        "conn_giftcode": "db/giftcode.sqlite",
        "conn_changes": "db/changes.sqlite",
        "conn_users": "db/users.sqlite",
        "conn_settings": "db/settings.sqlite",
    }

    connections = {name: sqlite3.connect(path) for name, path in databases.items()}

    print(Fore.GREEN + "Database connections have been successfully established." + Style.RESET_ALL)

    def create_tables():
        with connections["conn_changes"] as conn_changes:
            conn_changes.execute("""CREATE TABLE IF NOT EXISTS nickname_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                fid INTEGER, 
                old_nickname TEXT, 
                new_nickname TEXT, 
                change_date TEXT
            )""")
            
            conn_changes.execute("""CREATE TABLE IF NOT EXISTS furnace_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                fid INTEGER, 
                old_furnace_lv INTEGER, 
                new_furnace_lv INTEGER, 
                change_date TEXT
            )""")

        with connections["conn_settings"] as conn_settings:
            conn_settings.execute("""CREATE TABLE IF NOT EXISTS botsettings (
                id INTEGER PRIMARY KEY, 
                channelid INTEGER, 
                giftcodestatus TEXT 
            )""")
            
            conn_settings.execute("""CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY, 
                is_initial INTEGER
            )""")

        with connections["conn_users"] as conn_users:
            conn_users.execute("""CREATE TABLE IF NOT EXISTS users (
                fid INTEGER PRIMARY KEY, 
                nickname TEXT, 
                furnace_lv INTEGER DEFAULT 0, 
                kid INTEGER, 
                stove_lv_content TEXT, 
                alliance TEXT
            )""")

        with connections["conn_giftcode"] as conn_giftcode:
            conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
                giftcode TEXT PRIMARY KEY, 
                date TEXT
            )""")
            
            conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS user_giftcodes (
                fid INTEGER, 
                giftcode TEXT, 
                status TEXT, 
                PRIMARY KEY (fid, giftcode),
                FOREIGN KEY (giftcode) REFERENCES gift_codes (giftcode)
            )""")

        with connections["conn_alliance"] as conn_alliance:
            conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliancesettings (
                alliance_id INTEGER PRIMARY KEY, 
                channel_id INTEGER, 
                interval INTEGER
            )""")
            
            conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliance_list (
                alliance_id INTEGER PRIMARY KEY, 
                name TEXT
            )""")

        print(Fore.GREEN + "All tables checked." + Style.RESET_ALL)

    create_tables()

    async def load_cogs():
        cogs = ["olddb", "control", "alliance", "alliance_member_operations", "bot_operations", "logsystem", "support_operations", "gift_operations", "changes", "w", "wel", "other_features", "bear_trap", "id_channel", "backup_operations", "bear_trap_editor"]
        
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")

    @bot.event
    async def on_ready():
        try:
            print(f"{Fore.GREEN}Logged in as {Fore.CYAN}{bot.user}{Style.RESET_ALL}")
            await bot.tree.sync()
        except Exception as e:
            print(f"Error syncing commands: {e}")

    async def main():        
        await check_and_update_files()
        await load_cogs()
        
        await bot.start(bot_token)

    if __name__ == "__main__":
        asyncio.run(main())