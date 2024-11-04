

## Whiteout Survival Discord Bot V2

**I shared V1 a short while ago and I decided to improve it and the V2 version of our bot, which is more stable and more stable, with new features, is with you.**
#####  So what changes have happened?

**/gift**
First, let's talk about what's new in the gift command

The Gift command now shows the current gift codes when you type /gift and checks this periodically on github.
When there is a new gift command, your bot sends a private message to you and the people you added as admin.
When you use the gift command in a team of 100 people, it now saves the people who use it in the database.
In this way, when a new person joins your alliance, when you use the same gift command, if 99 people have used it, it skips 99 of them instantly.
In this way, we do not tire the API limits and when we want to try the gift command only on the newcomer, we do not need to check the remaining 99 people over and over again.
The following edit has been made about embed messages: The names of people who successfully use the Gift code will now appear, but people who have already used it or received an error will only be shown with a number
Thanks to this, we prevented unnecessary visual pollution

**/w**
This command allows you to see the details and pictures of the members you want, we have made updates in this command.
First of all, it was showing people above level 30, for example a person with FC level 8 as level 70.
We fixed this and now the FC level image will appear in the embed message according to the FC level.
When you type the w command, you will be able to see the contacts you saved in the database before sending and find them by typing their names (you can also type id if you want)
When using the /w command, you will be able to see under the embed message if the contact is registered in the database or not.
When the API limit is exceeded, you used to get an error when using the /w command, you will no longer get an error, it will make you wait until the API limit is exceeded and show you the result

**/addadmin **
We brought admin authorization to the codes that push API limits, the people you add as admin can only use the gift command, user addition and deletion commands.
**/nickname - /furnace**
**Now it saves every change in the database!**
It was already notifying you about people changing their name and skipping bakery levels, but now it records them.
When you type /nickname or /furnace it will ask you to enter id or select one of the users stored in the database.
You will be able to see how many times this person has changed their name and on which dates they used which name.
The same goes for /furnace (I don't know how useful it is for you :D )

**/allist**
When you wanted to see the alliance list, in an alliance of 100 people, this list was divided into 4-5 embeds, which turned into visual pollution.
We tried to make it quite minimal, there are still shifts in the names, this is because we cannot perceive the size of the characters in some different languages)

### I will now leave you with the visuals of the new commands
**`/allistadd`**
With this command you will add people to the alliance list, you can add 1 person at a time or 100 people at the same time
If you type /allistadd ID you will add only 1 person
You can write more than 1 id by putting a comma next to ID
/allistadd ID1,ID2,ID3,ID4
[![](https://github.com/Reloisback/test/blob/main/allistadd.png?raw=true)](https://github.com/Reloisback/test/blob/main/allistadd.png?raw=true)

**`/allist`**
With this command you can see your current alliance list
[![](https://github.com/Reloisback/test/blob/main/allist.png?raw=true)](https://github.com/Reloisback/test/blob/main/allist.png?raw=true)
**`/gift`**
With this command you can redeem the gift code to anyone you add to your alliance list. All of them will automatically receive the gift in their mail
[![](https://github.com/Reloisback/test/blob/main/gift1.png?raw=true)](https://github.com/Reloisback/test/blob/main/gift1.png?raw=true)
[![](https://github.com/Reloisback/test/blob/main/gift2.png?raw=true)](https://github.com/Reloisback/test/blob/main/gift2.png?raw=true)
[![](https://github.com/Reloisback/test/blob/main/gift3.png?raw=true)](https://github.com/Reloisback/test/blob/main/gift3.png?raw=true)
**`/nickname - /furnace`**
This command shows how many times the registered persons changed their name, when they changed it and what they changed it to
[![](https://github.com/Reloisback/test/blob/main/nicknamefurnace.png?raw=true)](https://github.com/Reloisback/test/blob/main/nicknamefurnace.png?raw=true)

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
