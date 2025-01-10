
<a href="https://www.buymeacoffee.com/reloisback" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
The current bot project is currently free as you know.
The current version and all future versions will always be free.
Updates may be delayed, but at the same time I'm working hard and trying to take care of my family, and I continue to develop the project whenever I can.
V2 may seem old but we are still sharing updates on discord, now V3.2 is shared on discord and I continue to develop V4 at the same time.

My coffee button is always active if you want to help.
I love you guys for using my bot and thank you very much for your nice messages
# Whiteout Survival Discord Bot V2

**I shared V1 a short while ago, and after some improvements, I'm introducing the more stable and feature-rich V2 version of the bot.**
[![How to Install? ](https://github.com/Reloisback/test/blob/main/howinstall.png?raw=true)](https://youtu.be/sWPjBpMhb3s)
### What's New?

### **/gift**
* The gift command now displays current gift codes when you type `/gift` and checks them periodically on GitHub.
* When there is a new gift code, the bot sends a private message to you and the people you’ve added as admins.
* When using this command in a team of 100 people, it records those who have already redeemed it, skipping them for future uses, thus conserving API limits.
* Embed message updates: Users who redeem the gift code successfully are shown by name, while those who already used it or encountered an error are displayed as a count.

### **/w**
* This command, which lets you view the details and images of specified members, has been updated.
* It now correctly shows the FC level, and the corresponding level image appears in the embed message.
* When you use `/w`, you can search for users by name or ID and view if they're registered in the database.
* If the API limit is reached, instead of an error, the bot waits and then displays the result.

### **/addadmin**
* Admin authorization has been added to limit API-heavy commands. Only admins can use the gift, add, and remove user commands.

### **/nickname - /furnace**
* Every change is now saved in the database. It previously notified you of name changes and furnace level updates, but now also records them.
* When using `/nickname` or `/furnace`, you can enter an ID or select a user from the database. You’ll see name change history, dates, and previous names.

### **/allist**
* Previously, viewing an alliance list of 100 people would divide it into 4-5 embeds, creating visual clutter. Now it’s more compact and minimal.

### Visuals of New Commands

#### **`/allistadd`**
* This command allows you to add people to the alliance list, either one by one or in batches.
* Use `/allistadd ID` for one person or `/allistadd ID1,ID2,ID3` for multiple entries.

![Allistadd](https://github.com/Reloisback/test/blob/main/allistadd.png?raw=true)

#### **`/allist`**
* This command shows your current alliance list.

![Allist](https://github.com/Reloisback/test/blob/main/allist.png?raw=true)

#### **`/gift`**
* Redeem the gift code for alliance members, delivering gifts directly to their mailbox.

![Gift 1](https://github.com/Reloisback/test/blob/main/gift1.png?raw=true)
![Gift 2](https://github.com/Reloisback/test/blob/main/gift2.png?raw=true)
![Gift 3](https://github.com/Reloisback/test/blob/main/gift3.png?raw=true)

#### **`/nickname - /furnace`**
* Shows the number of times a person changed their name and the dates.

![Nickname Furnace](https://github.com/Reloisback/test/blob/main/nicknamefurnace.png?raw=true)

## Description

This bot is developed for Whiteout Survival players to enhance their Discord channel experience.
The bot notifies you when Alliance members change their furnace level or in-game name.

---
![Furnace Level Changes](https://serioyun.com/gif/1.png)
![User Info](https://serioyun.com/gif/2.png)
![Nickname Changes](https://serioyun.com/gif/3.png)
![ALLIANCE LIST](https://serioyun.com/gif/4.png)

## How to Use?

Before starting, fill in the `settings.txt` with:
- `BOT_TOKEN` 
- `CHANNEL_ID` 
- `ALLIANCE_NAME`

**Do not modify the `SECRET` section!**

### Discord Commands

#### Adding and Removing Members

- To add a member:
```
/allistadd playerID
```

- To add multiple players:
```
/allistadd playerID1,playerID2,playerID3
```
Recommended limit: 10 additions at a time to avoid temporary API bans.

- To remove a member:
```
/allistremove playerID
```

- To view the alliance list:
```
/allist
```

- To manually update the list:
```
/updateallist
```

- For detailed player information and profile pictures:
```
/w playerID
```

*Note*: Avoid manual refreshes during alliance list updates.

To change the auto-update interval, modify the `@tasks.loop(minutes=20)` line to your desired interval.

---

## Support Information

This bot is freely provided by Reloisback for Whiteout Survival users on Discord.
If you need help, add Reloisback on Discord. For 24/7 setup help on a Windows server, contact me for free support.

To support future projects, consider donating:
- USDT Tron (TRC20): TC3y2crhRXzoQYhe3rMDNzz6DSrvtonwa3
- USDT Ethereum (ERC20): 0x60acb1580072f20f008922346a83a7ed8bb7fbc9

Thank you!


---

## Yapımcı Bilgisi

Merhaba, bu bot Reloisback tarafından 18.10.2024 tarihinde Whiteout Survival kullanıcılarının Discord kanallarında kullanması için ücretsiz olarak yapılmıştır.
Eğer Python kullanmayı bilmiyorsanız, Discord üzerinden Reloisback arkadaş olarak ekleyerek bana ulaşabilirsiniz; size yardımcı olmaktan mutluluk duyarım.
Eğer bir Windows sunucu satın alırsanız ve hala kurmayı bilmiyorsanız ve botun 7/24 çalışmasını istiyorsanız yine benimle iletişime geçebilirsiniz. Sizin için ücretsiz destek sağlayabilirim ve kurulumda yardımcı olabilirim.
Tekrar söylediğim gibi, bu kodlar tamamen ücretsizdir ve hiç kimseden ücret talep etmiyorum.

Fakat bir gün bana destek olmak isterseniz, işte coin bilgilerim;
- USDT Tron (TRC20): TC3y2crhRXzoQYhe3rMDNzz6DSrvtonwa3
- USDT Ethereum (ERC20): 0x60acb1580072f20f008922346a83a7ed8bb7fbc9

Desteklerinizi hiçbir zaman unutmayacağım ve bu tür projeleri ücretsiz bir şekilde geliştirmeye devam edeceğim.

Teşekkürler!
