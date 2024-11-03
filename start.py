import os
import sys
import subprocess
from colorama import Fore, Style, init
import webbrowser
import requests

init(autoreset=True)

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


def main_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(ascii_art)

        print(f"{Fore.GREEN}1. {Fore.WHITE}Start the Discord Bot")
        print(f"{Fore.GREEN}2. {Fore.WHITE}Install Libraries")
        print(f"{Fore.GREEN}3. {Fore.WHITE}Do you need support? Choose this one")
        print(f"{Fore.GREEN}4. {Fore.WHITE}Close")
        
        choice = input("\nOption (1, 2, 3, 4): ")

        if choice == "1":
            try:
                print("\nRunning the bot...\n")
                subprocess.run(["python", "main.py"])
            except Exception as e:
                print(f"{Fore.RED}Failed to start the bot: {e}")

        elif choice == "2":
            install_requirements()

        elif choice == "3":
            print(f"{Fore.YELLOW}You can join the official discord channel from the link for support.")
            subprocess.Popen(['cmd', '/c', 'start', 'https://dc.gg/whiteoutall'])
            input("Press Enter to return to the main menu...")

        elif choice == "4":
            print(f"{Fore.YELLOW}Closing the program...")
            sys.exit()
        
        else:
            print(f"{Fore.RED}Invalid option! Please enter 1, 2, 3 or 4.")
            input("Press Enter to return to the main menu...")

if __name__ == "__main__":
    main_menu()
