# alibru_search_bot telegram bot.
Try it out:
https://t.me/alibru_search_bot

So there's a popular in certain circles russian book dealers website https://www.alib.ru/ . It was created like an eternity ago, and I hate to use it, although using it pretty frequently, because it's a good source of rare editions.
I decided to make a little python project and created a telergam bot, that can search books on this site and give me results in a more convinient way.
Also I added a feature, that allows create a watchlist. The bot checks this watchlist twice a day after website database updated at 09:00 and 23:00 (GMT+3) and give you a notification, if something was found.
Original website realy lacks this feature.

This repositery contains 2 modules that make up the code of the bot:
  1) alib_search.py - Searching books on alib.ru and return a scrapping result in a nested list. 3rd-party packages used: bs4, requests;
  2) tbot_inline.py - Bot functions and deploying on heroku cloud with redis add-on. 3rd-party packages used: telebot, schedule, flask, redis.
