

# Whiteout Survival Bot

## Description

This bot is developed for Whiteout Survival players to enhance their Discord channel experience.
This bot will automatically tell you when members of your Alliance change their Furnace level or change their name in-game.

You can also see their profile photos larger than usual
---
![Furnace Level Changes](https://serioyun.com/gif/1.png)
![User Info](https://serioyun.com/gif/2.png)
![Nickname Changes](https://serioyun.com/gif/3.png)
![ALLIANCE LIST](https://serioyun.com/gif/4.png)
## How to Use?

When you first run the bot, don't forget to fill in the `settings.txt` file with:
- `BOT_TOKEN` 
- `CHANNEL_ID` 
- `ALLIANCE_NAME`

**Do not modify the `SECRET` section!**

### Discord Commands

#### Add and Remove Members

- To add a member, use the command:
```
/allistadd playerID
```

- To add multiple players at once, use:
```
/allistadd playerID1,PlayerID2,PlayerID3
```
It's recommended to limit to a maximum of 10 additions at a time to avoid temporary bans from the API.

- To remove a member, use:
```
/allistremove playerID
```

- To view the current list of your alliance, use:
```
/allist
```

- To manually update the alliance list, use:
```
/updateallist
```

- To access detailed information and profile picture of a player, use:
```
/w playerID
```

**Note:** While the bot updates the alliance list, please do not manually refresh it if you are also accessing a player's detailed profile.

To change the automatic update interval, you can modify the number in line 264 where it says `@tasks.loop(minutes=20)`. Changing it to `60` will set it to 1 hour. The recommended duration is 60 minutes; do not decrease it below 20 minutes, as checking 100 players takes approximately 5-10 minutes.

---

## Support Information

Hello, this bot is provided for free by Reloisback on October 18, 2024, for Whiteout Survival users in Discord channels.
If you are unfamiliar with Python and need assistance, feel free to contact me on Discord by adding Reloisback as a friend. I would be happy to help you.
If you purchase a Windows server and still need help with the setup for 24/7 bot operation, please reach out to me. I can provide free support and assistance with the installation.
As I mentioned, this code is completely free, and I do not charge anyone.

However, if you ever wish to support me, here are my coin details:
- USDT Tron (TRC20): TC3y2crhRXzoQYhe3rMDNzz6DSrvtonwa3
- USDT Ethereum (ERC20): 0x60acb1580072f20f008922346a83a7ed8bb7fbc9

I will never forget your support and will continue to develop such projects for free.

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
