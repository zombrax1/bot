# Whiteout Survival Discord Bot

This guide explains how to manually update your existing bot installation so that gift code redemption works again.

`v1.0.0` is the last version that needs to be patched manually. If you run this version, you will be able to update via the autoupdate system in the future.

This bot is a new, actively maintained version of the original bot created by Reloisback. You can find the original repository [here](https://github.com/Reloisback/Whiteout-Survival-Discord-Bot/blob/main/README.md).

## 🖥️ System Requirements & Prerequisites

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
 - **Are you installing for the first time?** Follow the instructions [for New Installations](https://github.com/whiteout-project/bot/tree/main?tab=readme-ov-file#-for-new-installations) instead.
 - If you run your bot on Windows, there is a known issue with onnxruntime + an outdated Visual C++ library. To overcome this, install [the latest version of Visual C++](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) and then run `main.py` again.
 - If you run your bot non-interactively, for example in a container or as a systemd service, you should run `main.py --autoupdate` to prevent the bot from using the interactive update prompt.
 - The current version of the bot will create a backup of your database folder to `db.bak` automatically during updates, so you do not need to worry about it anymore.

### For Existing Installations (Upgrading):

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
    *   Run the bot's startup command as you normally would (e.g., `python main.py`). *note: an update to v1.0.0 will show up, update to this to get the new patch*
    *   Observe the console output. This step might take a few minutes, depending on your internet connection.
    *   If the automatic installation completed successfully, the bot should continue starting up.
    *   **If the automatic installation fails:** Please contact the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

### For New Installations:

1.  **⬇️ Download the Complete Package:**
    *   Download the [full release page](https://github.com/whiteout-project/bot/archive/refs/tags/v1.0.0.zip)
    *   Extract the ZIP to a new directory where you want to run the bot

2.  **▶️ Start the Bot:**
    *   Open a terminal or command prompt **in your bot's main directory**.
    *   Run `python main.py` to start the bot
    *   If prompted for a Discord bot token, enter your bot token
    *   The bot should initialize and connect to Discord

3.  **🔧 Run Settings:**
    *   Remember to run /settings for the bot in Discord to configure yourself as the admin.

---

## 🧹 Post-Installation

*   The CAPTCHA solver should now be active. It has approximately 80% accuracy at the moment and is not as resource-intensive as EasyOCR.
*   In case any IDs end up with an Error result, you can always re-run the redemption for the same gift code and alliance again to hopefully redeem it successfully this time.
*   You can configure saving CAPTCHA images and other OCR settings via the bot's `/settings` -> Gift Code Operations -> CAPTCHA Settings menu.
*   You can monitor the bot's logs (`log/giftlog.txt` and `log/gift_ops.log`) for CAPTCHA-related messages during gift code processing.

If you encounter issues with this patch, reach out to the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

---

## 🛠️ Patch Notes 

### Version v1.0.0 (Current)

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