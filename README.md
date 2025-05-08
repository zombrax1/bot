# Whiteout Discord Bot

This guide explains how to manually update your existing bot installation so that gift code redemption works again.

`v2.0.0` is the last version that needs to be patched manually. If you run this version, you will be able to update via **(update process TBD)** in the future.

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

## Installation Steps

**IMPORTANT:** The current version of the bot will create a back up your database folder to db.bak automatically, so you no longer need to worry about it.

1.  **🛑 Stop the Bot:** Ensure your Discord bot `main.py` script is not currently running.

2.  **⬇️ Download Patch Files:**
    *   Download the updated Python files for the CAPTCHA patch. You will need these specific files:
        *   `main.py`
        *   `cogs/gift_operations.py`
        *   `cogs/gift_captchasolver.py`
    *   [Click here to download Patch Files - link TBD]()

3.  **🔄 Replace/Add Files:**
    *   Go to your bot's main directory.
    *   Replace the existing `main.py` with the downloaded `main.py`.
    *   Go into the `cogs` sub-directory.
    *   Replace the existing `gift_operations.py` with the downloaded one.
    *   Add the new `gift_captchasolver.py` file into the `cogs` directory, or replace it if it already exists.

4.  **▶️ Restart the Bot:**
    *   Open a terminal or command prompt **in your bot's main directory**.
    *   Run the bot's startup command as you normally would (e.g., `python main.py`).
    *   Observe the console output. This step might take a few minutes, depending on your internet connection.
    *   If the automatic installation completed successfully, the bot should continue starting up.
    *   **If the automatic installation fails:** Please contact the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

5.  **✅ Verify:**
    *   Check the bot's console output for any errors during startup, especially related to `GiftOperations` or `GiftCaptchaSolver`. Look for messages indicating whether the solver initialized successfully.
    *   Once the bot is online, try using the `/settings` command (or equivalent) and navigate to the Gift Code Operations menu to ensure it loads correctly. Check the OCR status under the `CAPTCHA Settings`.
    *   Test redeeming some gift codes. It should be working, although it may take a bit longer than before.

---

## 🧹 Post-Installation

*   The CAPTCHA solver should now be active. It has approximately 80% accuracy at the moment and is not as resource-intensive as EasyOCR.
*   In case any IDs end up with an Error result, you can always re-run the redemption for the same gift code and alliance again to hopefully redeem it successfully this time.
*   You can configure saving CAPTCHA images and other OCR settings via the bot's `/settings` -> Gift Code Operations -> CAPTCHA Settings menu.
*   You can monitor the bot's logs (`log/giftlog.txt` and `log/gift_ops.log`) for CAPTCHA-related messages during gift code processing.

If you encounter issues with this patch, reach out to the [project admins](https://github.com/orgs/whiteout-project/people) or open an issue on Github.

---

## 🛠️ Patch Notes 

### Version 2.0.0 (Current)

- 🔁 Replaced EasyOCR with ddddocr — Faster, lighter, smarter. Like trading a fax machine for a laser cannon.
- 🧹 Auto-cleans itself now — main.py will politely (and mercilessly) uninstall EasyOCR and its baggage. Then installs ddddocr like a boss.
- 🛠️ Force-installs ddddocr v1.5.6 with --ignore-requires-python — Because Python 3.13 broke it, but we broke it back.
- 🧠 Optimized gift code redemption loops — Now redeems faster while expertly dodging the rate-limit police.
- 🔥 Removed dusty old GPU config junk — No one needed it, especially not our new friend ddddocr. It’s in a nice farm upstate with the other unused settings.
- 🛡️ Bundled certifi in main.py — Fixes those annoying SSL issues on AWS and friends. Big thanks to @destrimna for reporting, rather than rage-quitting.
- 🧩 Fixed "All Alliances" feature — It works now. Because @destrimna sent in the fix. MVP.
- 📉 Trimmed log file bloat — Only keeps 1 backup now. Your hard drive can breathe a bit better.
- 📊 Improved OCR Settings statistics page — More stats. More clarity. Slightly less shame.
- ♻️ Fixed duplicate install checks on startup & updated main.py to work with our new repository. We pray that it works.

### Version 1.0.5

- ♻️ Improved robustness of the gift code channel monitoring:
  - If 4 redemption attempts fail, a ⏳ emoji is added, and the system retries in the next cycle.

- 🧹 Bug Fixes & Maintenance:
  - Fixed an error when saving all OCR images (previously required turning off image saving to avoid crash).
  - Reduced frequency of periodic gift code revalidation from every 5 minutes to **every 30 minutes** to reduce system load.
  - Final status update in the result embed is now always shown after redemption completes.
  - Switched `giftlog.txt` to use a proper logger with **log rotation** (3MB max, 3 backups).
  - Gift Code Operations menu text was updated to cover all buttons.

- 🧠 OCR and image processing improvements:
  - Decoupled image saving from OCR outcome: captcha images are saved once up front and renamed/deleted later based on result.
  - Captcha images from successful OCR are now saved as `<captcha>.png`.
  - Failed OCR attempts are saved (if enabled) as `FAIL_<captcha>_<timestamp>.png`.