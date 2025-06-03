import subprocess
import sys
import os

def is_container() -> bool:
    return os.path.exists("/.dockerenv") or os.path.exists("/var/run/secrets/kubernetes.io")

# Handle venv setup
if sys.prefix == sys.base_prefix and not is_container():
    print("Running the bot in a venv (virtual environment) to avoid dependency conflicts.")
    venv_path = "bot_venv"

    # Determine the python executable path in the venv
    if sys.platform == "win32":
        venv_python_name = os.path.join(venv_path, "Scripts", "python.exe")
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    else:
        venv_python_name = os.path.join(venv_path, "bin", "python")
        activate_script = os.path.join(venv_path, "bin", "activate")

    if not os.path.exists(venv_path):
        try:
            print("Attempting to create virtual environment automatically...")
            subprocess.check_call([sys.executable, "-m", "venv", venv_path], timeout=300)
            print(f"Virtual environment created at {venv_path}")

            if sys.platform == "win32":
                print("\nVirtual environment created.")
                print("To continue, please run the script again with the venv Python:")
                print(f"  1. Open CMD or PowerShell in this directory: {os.getcwd()}")
                print(f"  2. Run: {venv_python_name} {os.path.basename(sys.argv[0])}")
                sys.exit(0)
            else: # For non-Windows, try to relaunch automatically
                print("Restarting script in virtual environment...")
                venv_python_executable = os.path.join(venv_path, "bin", "python")
                os.execv(venv_python_executable, [venv_python_executable] + sys.argv)

        except Exception as e:
            print("Failed to create virtual environment automatically.")
            print(f"Error: {e}")
            print("Please create one manually with: python -m venv bot_venv")
            print("Then activate it and run this script again.")
            print("See also: https://docs.python.org/3/library/venv.html#how-venvs-work")
            sys.exit(1)
    else: # Venv exists
        if sys.platform == "win32":
            print(f"Virtual environment at {venv_path} exists.")
            print("To ensure you are using it, please run the script with the venv Python:")
            print(f"  1. Open CMD or PowerShell in this directory: {os.getcwd()}")
            print(f"  2. Run: {venv_python_name} {os.path.basename(sys.argv[0])}")
            sys.exit(0)
        else: # For non-Windows, if venv exists but we're not in it, try to relaunch
            venv_python_executable = os.path.join(venv_path, "bin", "python")
            if os.path.exists(venv_python_executable):
                print(f"Using existing virtual environment at {venv_path}. Restarting...")
                os.execv(venv_python_executable, [venv_python_executable] + sys.argv)
            else:
                print(f"Virtual environment at {venv_path} appears corrupted.")
                print("Please remove it and run the script again, or create a new one manually.")
                sys.exit(1)

try: # Import or install requests so we can get the requirements
    import requests
except ImportError:
    print("Installing requests (required for dependency management)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], 
                            timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import requests
    except Exception as e:
        print(f"Failed to install requests: {e}")
        print("Please install requests manually: pip install requests")
        sys.exit(1)

def ensure_requirements_file():
    """Ensure requirements.txt exists, download from latest release if needed."""
    if os.path.exists("requirements.txt"):
        return True
    
    print("requirements.txt not found. Downloading from latest release...")
    try:
        latest_release_url = "https://api.github.com/repos/whiteout-project/bot/releases/latest"
        latest_release_resp = requests.get(latest_release_url, timeout=30)
        
        if latest_release_resp.status_code == 200:
            latest_release_data = latest_release_resp.json()
            download_url = latest_release_data["assets"][0]["browser_download_url"]
            
            # Download and extract to get requirements.txt
            download_resp = requests.get(download_url, timeout=300)
            if download_resp.status_code == 200:
                with open("temp_package.zip", "wb") as f:
                    f.write(download_resp.content)
                
                import zipfile
                with zipfile.ZipFile("temp_package.zip", 'r') as zip_ref:
                    if "requirements.txt" in zip_ref.namelist():
                        zip_ref.extract("requirements.txt", ".")
                        print("Successfully downloaded requirements.txt")
                        
                        try:
                            os.remove("temp_package.zip")
                        except:
                            pass
                        
                        return True
                
                try:
                    os.remove("temp_package.zip")
                except:
                    pass
        
        print("Failed to download requirements.txt from release")
        return False
        
    except Exception as e:
        print(f"Error downloading requirements.txt: {e}")
        return False

def check_and_install_requirements():
    """Check each requirement and install missing ones."""
    if not os.path.exists("requirements.txt"):
        print("No requirements.txt found after download attempt")
        return False
        
    # Read requirements
    with open("requirements.txt", "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    print(f"Checking {len(requirements)} requirements...")
    
    missing_packages = []
    
    # Test each requirement
    for requirement in requirements:
        package_name = requirement.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("!=")[0]
        
        # Skip OCR-related packages for now
        if package_name.lower() in ["ddddocr", "opencv-python-headless", "numpy", "pillow", "onnxruntime"]:
            continue
            
        try:
            if package_name == "discord.py":
                import discord
            elif package_name == "aiohttp-socks":
                import aiohttp_socks
            elif package_name == "python-dotenv":
                import dotenv
            else:
                __import__(package_name)
                        
        except ImportError:
            print(f"✗ {package_name} - MISSING")
            missing_packages.append(requirement)
    
    if missing_packages: # Install missing packages
        print(f"Installing {len(missing_packages)} missing packages...")
        
        for package in missing_packages:
            try:
                cmd = [sys.executable, "-m", "pip", "install", package, "--no-cache-dir"]
                
                # Special handling for ddddocr on Python 3.13+
                if package.startswith("ddddocr") and sys.version_info >= (3, 13):
                    cmd.append("--ignore-requires-python")
                
                subprocess.check_call(cmd, timeout=1200, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✓ {package} installed successfully")
                
            except Exception as e:
                print(f"✗ Failed to install {package}: {e}")
                return False
    
    print("✓ All basic requirements satisfied")
    return True

def check_ocr_dependencies():
    """Check and install OCR-specific dependencies."""
    print("Checking OCR dependencies...")
        
    missing_ocr = []
    
    # Test OCR imports
    try:
        import numpy
    except ImportError:
        print("✗ numpy - MISSING")
        missing_ocr.append("numpy")
    
    try:
        import PIL
    except ImportError:
        print("✗ Pillow - MISSING")
        missing_ocr.append("Pillow")
    
    try:
        import cv2
    except ImportError:
        print("✗ opencv-python-headless - MISSING")
        missing_ocr.append("opencv-python-headless")
    
    try:
        import onnxruntime
    except ImportError:
        print("✗ onnxruntime - MISSING")
        missing_ocr.append("onnxruntime")
    
    try:
        import ddddocr
    except ImportError:
        print("✗ ddddocr - MISSING")
        missing_ocr.append("ddddocr==1.5.6")
    
    # Install missing OCR packages
    if missing_ocr:
        print(f"Installing {len(missing_ocr)} missing OCR packages...")
        
        for package in missing_ocr:
            try:
                cmd = [sys.executable, "-m", "pip", "install", package, "--no-cache-dir"]
                
                if package.startswith("ddddocr") and sys.version_info >= (3, 13):
                    cmd.append("--ignore-requires-python")
                
                subprocess.check_call(cmd, timeout=600, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✓ {package} installed successfully")
                
            except Exception as e:
                print(f"✗ Failed to install {package}: {e}")
    
    # Test OCR object creation
    try:
        import ddddocr
        ocr = ddddocr.DdddOcr(show_ad=False)
        return True
    except Exception as e:
        print(f"✗ OCR object creation failed: {e}")
        if "DLL" in str(e):
            print("Visual C++ Redistributable may be missing or outdated.")
            print("Please install latest 64-bit from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return False

def setup_dependencies():
    """Main function to set up all dependencies."""
    print("Starting dependency check...")
    
    # Ensure requirements.txt exists
    if not ensure_requirements_file():
        print("Failed to obtain requirements.txt")
        return False
    
    # Check and install basic requirements
    if not check_and_install_requirements():
        print("Failed to install basic requirements")
        return False
    
    # Check and install OCR dependencies
    ocr_success = check_ocr_dependencies()
    if not ocr_success:
        print("OCR setup failed, but continuing with basic functionality")
    
    print("Dependency check completed...")
    return True

if not setup_dependencies():
    print("Dependency setup failed. Please install manually with: pip install -r requirements.txt")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    import discord
    print("✓ All core imports successful")
except ImportError as e:
    print(f"Import failed even after dependency setup: {e}")
    print("Please restart the script or install dependencies manually")
    sys.exit(1)

import warnings
import shutil

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

    def install_packages(requirements_txt_path: str, debug: bool = False) -> bool:
        """Install packages from requirements.txt file."""
        with open(requirements_txt_path, "r") as f: 
            lines = [line.strip() for line in f]
        
        success = []
            
        for dependency in lines:
            full_command = [sys.executable, "-m", "pip", "install", dependency, "--no-cache-dir", "--force-reinstall"]
            
            if dependency.startswith("ddddocr") and (sys.version_info.major == 3 and sys.version_info.minor >= 13):
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
        
    import asyncio
    from datetime import datetime
            
    asyncio.run(check_and_update_files())
            
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