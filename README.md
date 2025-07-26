# Whiteout Survival Discord Bot

**Update July 09, 2025**

- Restricted server admin alliance views to show only alliances from the current server or those explicitly added for them.
- Fixed admin alliance visibility so permissions are applied correctly.

Whiteout Survival Discord Bot that supports alliance management, event reminders, gift code redemption and more.

This guide explains how to manually update your existing bot installation so that gift code redemption works again.

`v1.0.0` is the last version that needs to be patched manually. If you run this version, you will be able to update via the autoupdate system in the future.

This bot is a new, actively maintained version of the original bot created by Reloisback.

## Installation

### 🖥️ System Requirements & Prerequisites

After switching to ONNX based [ddddocr](https://github.com/sml2h3/ddddocr), system requirements has significantly decreased from patch v1.0.5. Here are the following requirements:

| Prerequisite  | Minimum                                     | Recommended                                   |
|---------------|---------------------------------------------|-----------------------------------------------|
| CPU           | AMD64 Processor with SSE4.1 Support (2008+) or Any ARM64 Processor | AMD64 Processor with AVX/AVX2 Support (2013+) or Any ARM64 Processor |
| Memory        | 200 MB Free RAM                             | 1 GB for smoother operation                   |
| Disk Space    | 500 MB (OCR and other packages)             | SSD for faster OCR performance                |
| GPU           | None                                        | None                                          |
| Python        | 3.9                                         | 3.12 or 3.12.x                                |


*   An existing, functional installation of the [Whiteout Survival Discord Bot](https://github.com/Reloisback/Whiteout-Survival-Discord-Bot) (with or without the v1.0.5 patch).
*   Access to the server or machine where the bot is running.
*   Python and pip installed on the system running the bot (should be already if the bot is working).

---

## 🚀 Installation Steps

### ⚠️ **IMPORTANT ⚠️**
 - **Are you installing for the first time?** Follow the instructions [for New Installations](https://github.com/whiteout-project/bot?tab=readme-ov-file#for-new-installations) instead.
 - If you run your bot on Windows, there is a known issue with onnxruntime + an outdated Visual C++ library. To overcome this, install [the latest version of Visual C++](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) and then run `main.py` again.
 - If you run your bot non-interactively, for example in a container or as a systemd service, you should run `main.py --autoupdate` to prevent the bot from using the interactive update prompt.
 - The current version of the bot will create a backup of your database folder to `db.bak` automatically during updates, so you do not need to worry about it anymore.

### ⚠️ Python 3.13 Users: Read This or Else!
- **`ddddocr` still doesn’t support Python 3.13+.**  
  → Please try Python 3.12 if you hit OCR-related dependency issues.  
  (We know. It’s tragic. But it works.)

### ⚠️ Alpine Container Base - Not Supported!
- Some container hosting platforms (such as KataBump) may run into **disk space issues** during installation, even if sufficient space appears to be available.  
- This typically occurs because these platforms use **Alpine Linux** or similar Linux distro, which does not include the standard `glibc` C library. As a result, dependencies like [OpenCV](https://pypi.org/project/opencv-python-headless/) lack pre-built wheels for this environment, forcing Python to compile them from source. The build process consumes **several gigabytes of disk space**, typically exceeding the container's limits and causing installation to fail.  
- ✅ To avoid this, consider using a container base image that includes `glibc`.

---

### Upgrading Existing Installations
Running v1.0.0 or higher already:

- If you **already have a working instance**: just restart the bot. It will either update automatically or prompt you, depending on your `--autoupdate` setting.
- If your **instance was previously stuck or broken**: download the latest [main.py](<https://github.com/whiteout-project/bot/blob/v1.1.0/main.py>) and overwrite your existing one. It will handle requirement installation for you.

---

### Upgrading Legacy Installations
Upgrading from the "Relo/Patch Versions" before 1.0.0:

1.  **🛑 Stop the Bot:** Ensure your Discord bot's `main.py` script is not currently running.

2.  **🗑️ Uninstall old OCR Packages:**
    *   Run this command in your terminal: `pip uninstall -y easyocr torch torchvision torchaudio opencv-python`

3.  **⬇️ Download Patch Files:**
    *   Download the updated Python files for the CAPTCHA patch. You will need these specific files:
        *   `main.py`
    *   [Click here and download the patched main.py](https://github.com/whiteout-project/bot/blob/main/main.py)

4.  **🔄 Replace/Add Files:**
    *   Go to your bot's main directory.
    *   Replace the existing `main.py` with the downloaded `main.py`.

5.  **▶️ Restart the Bot:**
    *   Open a terminal or command prompt **in your bot's main directory**.
    *   Run the bot's startup command as you normally would (e.g., `python main.py`). *Note: an update to v1.1.0 will show up, enter 'y' to get the new patch*
    *   Observe the console output. This step might take a few minutes, depending on your internet connection.
    *   If the automatic installation completed successfully, the bot should continue starting up.
    *   **If the automatic installation fails:** Please contact the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

---

### For New Installations:

1.  **⬇️ Download the Installer:**
    *   Download the [install.py file](https://github.com/whiteout-project/install/blob/main/install.py)
    *   Place it in a new directory where you want to run the bot

2.  **▶️ Start the Installer:**
    *   Open a terminal or command prompt **in the new directory you created where install.py is located**.
    *   Run `python install.py` to install the bot. This should automatically pull main.py and other files into the directory.

3.  **▶️ Start the Bot:**
    *   In your terminal or command prompt **in the same directory you created**, run `python main.py` to start the bot.
    *   When prompted for a Discord bot token, enter your bot token. The bot should now initialize and connect to Discord.

4.  **🔧 Run /settings in Discord:**
    *   Remember to run /settings for the bot in Discord to configure yourself as the admin.

---

## 🧹 Post-Installation

*   The CAPTCHA solver should now be active. It has approximately 80% accuracy at the moment and is not as resource-intensive as EasyOCR.
*   In case any IDs end up with an Error result, you can always re-run the redemption for the same gift code and alliance again to hopefully redeem it successfully this time.
*   You can configure saving CAPTCHA images and other OCR settings via the bot's `/settings` -> Gift Code Operations -> CAPTCHA Settings menu.

## Logs

The bot records its activity in the `log/` directory. Key files include:
- `log/giftlog.txt` – details each gift code redemption attempt
- `log/gift_ops.log` – general operations log

Use these logs to troubleshoot issues or confirm successful redemptions.

If you encounter issues with this patch, reach out to the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

---

## Features

- Self-hosted GitLab fallback for updates
- Automatic virtual environment management
- Built-in backup options (Discord DM or server files)

See [Patch Notes](#-patch-notes) for complete details.

## 🛠️ Patch Notes 

### Version v1.2.0 (Current)
- Implemented a **self-hosted GitLab repo** as a backup in case GitHub fails us again.  
- The bot now checks GitHub first, then falls back to GitLab if needed.
- The bot **automatically creates and manages Python virtual environments**.  
- Prevents dependency conflicts and ensures smooth setup.  
- Fully supports both Windows and Unix-based systems.  
- Automatically skips venv creation inside Docker/Kubernetes/CI environments.
- Better troubleshooting help, including the direct Visual C++ Redistributable x64 link.
- Startup now **auto-reinstalls dependencies** if broken or missing on startup.
- It also **auto-installs missing cogs** from source if they are not found on startup.
- Should reduce install/update issues across the board.
- Web editor? History, at least for now.
- Thanks to @Destrimna, you can now manage all notifications directly via Discord buttons.
- Old notifications (Embed or Message) remain fully editable.
- Added **“Repeat on specific days”** for recurring event scheduling.
- 🎟️ Added claim tracking database and `/claimreport` for summarizing gift code redemptions.
- Replaced the crusty old `wosland.com` PHP API with a modern, self-hosted Python version. (it's almost the same, but it smells new)
- Gift codes now **auto-sync across all bot instances** again. Enjoy the easy and efficient shared redeeming!
- Includes solid validation logic to block broken or invalid codes before they break the system.
- Redemptions now follow **alliance order** instead of chaotic parallel execution.  
- Fixed the dreaded “Sign Error” caused by sneaky right-to-left (RTL) marker characters
- Removed dependency on external websites for backup creation.
- Two backup options now available. Sent to you directly via Discord DM or saved manually to the server
- Backups are 100% under your control. Use it wisely. Or don't.
- Removed all remaining **Relo branding** from Support and Startup.
- Startup now proudly shows off **OCR status** like it's something to brag about.
- Removed outdated “Buy me a coffee” link. No coffee for scammers. ☕🚫
- **"Check for Updates"** button works again and compares your version file with the latest release tag on our Github.
- Tons of minor fixes and improvements.
- For the full list of ~~bugs~~ features, visit [GitHub Issues](https://github.com/whiteout-project/bot/issues)

### Version v1.1.0

- 💾 **More robust file handling & backups during updates**  
  Now gracefully sidesteps Windows' favorite pastime: locking files for no reason. May your `main.py` live a long, crash-free life.
- ✅ **`ddddocr` installation verification added**  
  Checks that `ddddocr` and its clingy dependencies are *actually* installed. No more “I installed it, I swear” gaslighting.
- 🎯 **Selective `--ignore-requires-python` usage**  
  Only applies the Python rule-bending to `ddddocr`, instead of every package. Because not every package needs special treatment.
- 🐛 **Verbose flag added for package installs**  
  Need to know exactly how the package installation broke? There’s a --verbose flag for that now.
- 🧾 **Added `colorama` and `requests` to requirements**  
  Two more packages join the cult. Because everything is better when you add some color to it.
- 🚫 **Gift code validation delayed to redemption time**  
  Codes added via "Create Gift Code" or the Gift Code Channel are no longer validated immediately. Instead:
  - They are stored in DB with status `pending`
  - On first use (or during periodic validation):
    - If valid: ✅ marked as `valid`
    - If invalid: ❌ redemption stops, status updated to `invalid`
  - Only validated codes hit the giftcode API (once implemented), reducing unnecessary API traffic.
- 🔄 **New “Change Test FID” button for admins**  
  Admins can now swap out the test ID used for validating and testing codes. Default: Relo’s ID. Change it. Or don’t. I’m not your dad.
- 🔙 **Removed Yolo’s favorite back button from CAPTCHA Settings**  
  The back button on CAPTCHA Settings is gone. Yes, really. It’s gone. Are you happy now, @Destrimna?
- 🐞 **Miscellaneous bug fixes**  
  Squashed several minor but persistent gremlins.
- 📣 **Bear Trap notifications now persist even if the channel disappears**  
  Previously, if the channel went poof (due to temporary Discord rate limits, for example), all notifications got disabled. That’s been fixed.

### Version v1.0.0

- 🔁 Replaced EasyOCR with ddddocr — Faster, lighter, smarter. Like trading a fax machine for a laser cannon.
- 🛠️ Force-installs ddddocr v1.5.6 with --ignore-requires-python — Because Python 3.13 broke it, but we broke it back.
- 🧠 Optimized gift code redemption loops — Now redeems faster while expertly dodging the rate-limit police.
- 🔥 Removed dusty old GPU config junk — No one needed it, especially not our new friend ddddocr. It’s in a nice farm upstate with the other unused settings.
- 🛡️ Bundled certifi in main.py — Fixes those annoying SSL issues on AWS and friends. Big thanks to @destrimna for reporting, rather than rage-quitting.
- 🧩 Fixed "All Alliances" feature — It works now. Because @destrimna sent in the fix. MVP.
- 📉 Trimmed log file and legacy file bloat — Your hard drive can breathe a bit better.
- 📊 Improved OCR Settings statistics page — More stats. More clarity. Slightly less shame.
- ♻️ Fixed duplicate install checks on startup & updated main.py to work with our new repository and update method. We pray that it works.
- ⬇️ Reset the version numbering to start from 1.0.0 for a clean slate. And better vibes. Mostly for the vibes.
