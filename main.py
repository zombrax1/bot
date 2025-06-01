import subprocess
import sys

if "linux" in sys.platform and sys.prefix == sys.base_prefix:
    print("please run this script in a venv (virtual environment) to avoid dependency conflicts.")
    sys.exit(0)

try:
    from colorama import Fore, Style, init
    import requests
except ImportError:
    print("Installing required dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama", "requests"], timeout=1200)
        print("Dependencies installed successfully. Please restart the script.")
        sys.exit()
    except Exception as _:
        print("Failed to install required dependencies. Please install them with \"pip install colorama requests\"")

import warnings
import shutil
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
            
    def is_container() -> bool:
        return os.path.exists("/.dockerenv") or os.path.exists("/var/run/secrets/kubernetes.io")
        
    def install_packages(requirements_txt_path: str, debug: bool = False) -> bool:
        with open(requirements_txt_path, "r") as f: 
            lines = [line.strip() for line in f]
        
        success = []
            
        for dependency in lines:
            full_command = [sys.executable, "-m", "pip", "install", dependency, "--no-cache-dir", "--force-reinstall"]
            
            if dependency.startswith("ddddocr") and (sys.version_info.major == 3 and sys.version_info.minor == 13):
                full_command = full_command + ["--ignore-requires-python"]
        
            try:
                if debug:
                    subprocess.check_call(full_command, timeout=1200)
                else:
                    subprocess.check_call(full_command, timeout=1200, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                success.append(0)
            except Exception as _:
                success.append(1)
                
        return sum(success) == 0

    def safe_remove_file(file_path):
        """Safely remove a file if it exists."""
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
                return True
            except PermissionError:
                print(Fore.YELLOW + f"Warning: Access Denied. Could not remove '{file_path}'. Check permissions or if file is in use." + Style.RESET_ALL)
            except OSError as e:
                print(Fore.YELLOW + f"Warning: Could not remove '{file_path}': {e}" + Style.RESET_ALL)
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
                
                if not is_container():
                    if "--autoupdate" in sys.argv:
                        update = True
                    else:
                        print("Note: If your terminal is not interactive, you can use the --autoupdate argument to skip this prompt.")
                        ask = input("Do you want to update? (y/n): ").strip().lower()
                        update = ask == "y"
                else:
                    print(Fore.YELLOW + "Running in a container. Skipping update prompt." + Style.RESET_ALL)
                    update = True
                    
                if update:
                    if os.path.exists("db") and os.path.isdir("db"):
                        print(Fore.YELLOW + "Making backup of database..." + Style.RESET_ALL)
                        
                        db_bak_path = "db.bak"
                        if os.path.exists(db_bak_path) and os.path.isdir(db_bak_path):
                            try:
                                shutil.rmtree(db_bak_path)
                            except (PermissionError, OSError) as e: # Create a timestamped backup to avoid upgrading without first having a backup
                                db_bak_path = f"db.bak_{int(datetime.now().timestamp())}"
                                print(Fore.YELLOW + f"WARNING: Couldn't remove db.bak folder: {e}. Making backup with timestamp instead." + Style.RESET_ALL)

                        try:
                            shutil.copytree("db", db_bak_path)
                            print(Fore.GREEN + f"Backup completed: db → {db_bak_path}" + Style.RESET_ALL)
                        except Exception as e:
                            print(Fore.RED + f"WARNING: Failed to create database backup: {e}" + Style.RESET_ALL)
                                            
                    download_url = latest_release_data["assets"][0]["browser_download_url"]
                    safe_remove_file("package.zip")
                    download_resp = requests.get(download_url)
                    
                    if download_resp.status_code == 200:
                        with open("package.zip", "wb") as f:
                            f.write(download_resp.content)
                        
                        if os.path.exists("update") and os.path.isdir("update"):
                            try:
                                shutil.rmtree("update")
                            except (PermissionError, OSError) as e:
                                print(Fore.RED + f"WARNING: Could not remove previous update directory: {e}" + Style.RESET_ALL)
                                return
                            
                        try:
                            shutil.unpack_archive("package.zip", "update", "zip")
                        except Exception as e:
                            print(Fore.RED + f"ERROR: Failed to extract update package: {e}" + Style.RESET_ALL)
                            return
                            
                        safe_remove_file("package.zip")
                        
                        if os.path.exists("update/main.py"):
                            try:
                                if os.path.exists("main.py.bak"):
                                    os.remove("main.py.bak")
                            except Exception as _:
                                pass
                                
                            try:
                                if os.path.exists("main.py"):
                                    os.rename("main.py", "main.py.bak")
                            except Exception as e:
                                print(Fore.YELLOW + f"Could not backup main.py: {e}" + Style.RESET_ALL)
                                try: # If backup fails, just remove the current file
                                    if os.path.exists("main.py"):
                                        os.remove("main.py")
                                        print(Fore.YELLOW + "Removed current main.py" + Style.RESET_ALL)
                                except Exception as _:
                                    print(Fore.RED + "Warning: Could not backup or remove current main.py" + Style.RESET_ALL)
                            
                            try:
                                shutil.copy2("update/main.py", "main.py")
                            except Exception as e:
                                print(Fore.RED + f"ERROR: Could not install new main.py: {e}" + Style.RESET_ALL)
                                return
                            
                        if os.path.exists("update/requirements.txt"):                      
                            print(Fore.YELLOW + "Installing new requirements..." + Style.RESET_ALL)
                            
                            success = install_packages("update/requirements.txt", debug="--verbose" in sys.argv or "--debug" in sys.argv)
                            safe_remove_file("update/requirements.txt")
                            
                            if success:
                                print(Fore.GREEN + "Requirements installed." + Style.RESET_ALL)
                            else:
                                print(Fore.RED + "Failed to install requirements." + Style.RESET_ALL)
                                return
                            
                        for root, _, files in os.walk("update"):
                            for file in files:
                                rel_path = os.path.relpath(os.path.join(root, file), "update")
                                dst_path = os.path.join(".", rel_path)
                                
                                os.makedirs(os.path.dirname(dst_path), exist_ok=True)

                                if os.path.exists(dst_path):
                                    backup_path = f"{dst_path}.bak"
                                    safe_remove_file(backup_path)
                                    try:
                                        os.rename(dst_path, backup_path)
                                    except Exception as e: # Continue anyway to try to update the file
                                        print(Fore.YELLOW + f"Could not create backup of {dst_path}: {e}" + Style.RESET_ALL)
                                        
                                try:
                                    shutil.copy2(os.path.join(root, file), dst_path)
                                except Exception as e:
                                    print(Fore.RED + f"Failed to copy {file} to {dst_path}: {e}" + Style.RESET_ALL)
                        
                        try:
                            shutil.rmtree("update")
                        except Exception as e:
                            print(Fore.RED + f"WARNING: update folder could not be removed: {e}. You may want to remove it manually." + Style.RESET_ALL)
                        
                        with open("version", "w") as f:
                            f.write(latest_tag)
                        
                        print(Fore.GREEN + "Update completed successfully. Restarting bot..." + Style.RESET_ALL)
                        restart_bot()
                    else:
                        print(Fore.RED + "Failed to download the update. HTTP status: {download_resp.status_code}" + Style.RESET_ALL)
                        return  
        else:
            print(Fore.RED + f"Failed to fetch latest release info. HTTP status: {latest_release_resp.status_code}" + Style.RESET_ALL)
            
    def check_dependencies():
        try:
            # First check if imports work
            verify_command = "import numpy; import PIL; import cv2; import onnxruntime; import ddddocr; print('All OCR dependencies imported successfully!')"
            result = subprocess.run([sys.executable, "-c", verify_command], 
                                capture_output=True, text=True)
            
            # If verification fails, try to install dependencies
            if result.returncode != 0:
                print(Fore.YELLOW + "OCR dependencies missing. Installing..." + Style.RESET_ALL)
                
                # Install dependencies individually
                dependencies = ["numpy", "Pillow", "opencv-python-headless", "onnxruntime"]
                
                for dep in dependencies:
                    try:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install", 
                            dep, "--no-cache-dir", "--force-reinstall"
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
                    except Exception as _:
                        pass
                
                # Install ddddocr with special handling on Python 3.13+
                try:
                    cmd = [sys.executable, "-m", "pip", "install", "ddddocr==1.5.6", 
                        "--no-cache-dir", "--force-reinstall"]
                    if sys.version_info.major == 3 and sys.version_info.minor >= 13:
                        cmd.append("--ignore-requires-python")
                    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
                except Exception as _:
                    pass
                
                # Retry verification after installation
                result = subprocess.run([sys.executable, "-c", verify_command], 
                                    capture_output=True, text=True)
            
            if result.returncode == 0:
                print(Fore.GREEN + "All OCR dependencies verified!" + Style.RESET_ALL)
                
                # Check if we can create a ddddocr object
                ocr_test_command = "import ddddocr\ntry:\n    ocr = ddddocr.DdddOcr(show_ad=False)\n    print(\"OCR object created successfully\")\nexcept Exception as e:\n    print(f\"Error creating OCR object: {e}\")\n    exit(1)"
                result = subprocess.run([sys.executable, "-c", ocr_test_command], 
                                    capture_output=True, text=True)
                
                if "OCR object created successfully" in result.stdout:
                    print(Fore.GREEN + "OCR object creation verified!" + Style.RESET_ALL)
                    return True
                else:
                    print(Fore.RED + f"OCR object creation failed: {result.stderr}" + Style.RESET_ALL)
                    if "DLL" in result.stderr:
                        print(Fore.YELLOW + "Visual C++ Redistributable may be missing or outdated." + Style.RESET_ALL)
                        print(Fore.YELLOW + "Please install the latest Visual C++ Redistributable from Microsoft:" + Style.RESET_ALL)
                        print(Fore.YELLOW + "https://aka.ms/vs/17/release/vc_redist.x64.exe" + Style.RESET_ALL)
                        print(Fore.YELLOW + "Make sure to install the 64-bit version for most systems!" + Style.RESET_ALL)
                    else:
                        print(Fore.YELLOW + "OCR initialization failed. This might affect CAPTCHA solving." + Style.RESET_ALL)
                    return False
            else:
                print(Fore.RED + f"OCR dependencies verification failed: {result.stderr}" + Style.RESET_ALL)
                return False
                
        except Exception as e:
            print(Fore.RED + f"OCR dependencies verification failed: {e}" + Style.RESET_ALL)
            return False
    
    import asyncio
    from datetime import datetime
            
    asyncio.run(check_and_update_files())
    check_dependencies()
            
    import discord
    from discord.ext import commands
    import sqlite3

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
        await load_cogs()
        
        await bot.start(bot_token)

    if __name__ == "__main__":
        asyncio.run(main())