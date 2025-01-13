import os
import sys
import subprocess

required_modules = ['colorama', 'requests']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if 'colorama' not in missing_modules:
    from colorama import Fore, Style, init
    init(autoreset=True)
else:
    class Fore:
        CYAN = BLUE = LIGHTRED_EX = GREEN = YELLOW = RED = WHITE = ""

ascii_art = f"""
{Fore.CYAN}  
 \ \        / / |  | |_   _|__   __|  ____/ __ \| |  | |__   __|      
  \ \  /\  / /| |__| | | |    | |  | |__ | |  | | |  | |  | |         
   \ \/  \/ / |  __  | | |    | |  |  __|| |  | | |  | |  | |         
    \  /\  /  | |  | |_| |_   | |  | |___| |__| | |__| |  | |         
   __\/_ \/   |_|__|_|_____| _|_|__|______\____/ \____/   |_|         
  / ____| |  | |  __ \ \    / /_   _\ \    / /\   | |                 
 | (___ | |  | | |__) \ \  / /  | |  \ \  / /  \  | |                 
  \___ \| |  | |  _  / \ \/ /   | |   \ \/ / /\ \ | |                 
  ____) | |__| | | \ \  \  /   _| |_   \  / ____ \| |____             
 |_____/_\____/|_|__\_\__\/ __|_____|__ \/_/__  \_\______|
 {Fore.BLUE}
 |  __ \_   _|/ ____|/ ____/ __ \|  __ \|  __ \  |  _ \ / __ \__   __|
 | |  | || | | (___ | |   | |  | | |__) | |  | | | |_) | |  | | | |   
 | |  | || |  \___ \| |   | |  | |  _  /| |  | | |  _ <| |  | | | |   
 | |__| || |_ ____) | |___| |__| | | \ \| |__| | | |_) | |__| | | |   
 |_____/_____|_____/ \_____\____/|_|  \_\_____/  |____/ \____/  |_|   
 {Fore.LIGHTRED_EX}
   _   _   _   _   _   _   _   _   _   _  
  / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ 
 ( R | E | L | O | I | S | B | A | C | K )
  \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ 
"""

def install_requirements():
    try:
        print("Installing libraries from requirements.txt...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        missing_modules.clear()

        global Fore, Style, init
        from colorama import Fore, Style, init
        init(autoreset=True)
        
        print(f"{Fore.GREEN}Libraries installed successfully!{Fore.WHITE}")

    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to install libraries: {e}")

def main_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(ascii_art)

        if missing_modules:
            print(f"{Fore.GREEN}1. {Fore.WHITE}Install Required Libraries")
            print(f"{Fore.GREEN}2. {Fore.WHITE}Exit")
            choice = input("\nOption (1 or 2): ")

            if choice == "1":
                install_requirements()
            elif choice == "2":
                print(f"{Fore.YELLOW}Exiting program...")
                sys.exit()
            else:
                print(f"{Fore.RED}Invalid option! Please enter 1 or 2.")
                input("Press Enter to return to the main menu...")

        else:
            print(f"{Fore.GREEN}1. {Fore.WHITE}Start Discord Bot")
            print(f"{Fore.GREEN}2. {Fore.WHITE}Install Libraries")
            print(f"{Fore.GREEN}3. {Fore.WHITE}Need support? Open the link")
            print(f"{Fore.GREEN}4. {Fore.WHITE}Exit")
            choice = input("\nOption (1, 2, 3, or 4): ")

            if choice == "1":
                try:
                    print("\nStarting the bot...\n")
                    subprocess.run(["python", "main.py"])
                except Exception as e:
                    print(f"{Fore.RED}Failed to start the bot: {e}")

            elif choice == "2":
                install_requirements()

            elif choice == "3":
                print(f"{Fore.YELLOW}You can join the official Discord channel for support.")
                subprocess.Popen(['cmd', '/c', 'start', 'https://dc.gg/whiteoutall'])
                input("Press Enter to return to the main menu...")

            elif choice == "4":
                print(f"{Fore.YELLOW}Exiting program...")
                sys.exit()

            else:
                print(f"{Fore.RED}Invalid option! Please enter 1, 2, 3, or 4.")
                input("Press Enter to return to the main menu...")

if __name__ == "__main__":
    main_menu()

