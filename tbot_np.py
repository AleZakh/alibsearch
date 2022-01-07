# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code for telegram-bor @alibru_search_bot.

import alib_search
import telebot
from telebot import types
import csv

# import schedule
# import time


#with open('bot_token.txt') as t:
#    token = t.read()
user_list = []

bot = telebot.TeleBot(token, parse_mode=None)

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    user_list.clear()
    user_list.append(message.chat.id)
    msg = bot.reply_to(message, """\
Hi!
Do you want to search for books or add one to a watchlist?
""", reply_markup=search_add_markup())
    bot.register_next_step_handler(msg, second_step)


def second_step(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    user_list.append(message.text)

    # if message.text == 'my watchlist':
    #     with open('watchlist.csv', 'r', encoding='utf-8') as wl:
    #         reader = csv.reader(wl)
    #         wl_msh=f'{row[2]} for less than {row[3]} rub /n' for row in reader if row[0]==user_list[0]'
    #         wl_msg='Your watchlist:/n'
    #         for row in reader:
    #         msg = bot.send_message(message, wl_msg, reply_markup=watchlist_markup())
    #     bot.register_next_step_handler(msg, my_watchlist())
    #     return

    msg = bot.reply_to(message, """\
Input author or/and book name in russian:
""", reply_markup=markup)
    bot.register_next_step_handler(msg, name_step)


def name_step(message):
    try:
        user_list.append(message.text)
        msg = bot.reply_to(message, 'Max price?')
        bot.register_next_step_handler(msg, price_step)
    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again")
        restart(message.chat.id)


def price_step(message):
    try:
        if not message.text.isdigit():
            msg = bot.reply_to(message, 'Price should be a number. So... max price?')
            bot.register_next_step_handler(msg, price_step)
            return

        price = int(message.text)
        user_list.append(price)
        print(user_list)

        if user_list[1] == 'add to watchlist':
            add_to_watchlist()
            return

        result = alib_search.main(user_list[2])

        if not result:
            bot.send_message(message.chat.id, f'Nothing was found on alib.ru. Try another author or/and book name')
        else:
            minprice = alib_search.minprice(result)
            user_list.append(minprice)
            if minprice > price:
                msg = bot.send_message(message.chat.id, f'''
                Nothing was found in your price range (<{price} руб)
                Minimal price is {minprice}.
                Show minimal price positions?
                ''', reply_markup=yes_no_markup())
                bot.register_next_step_handler(msg, lambda m: altprice_step(m, result, minprice))
            else:
                show_result(message.chat.id, result, price)


    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again")
        restart(message.chat.id)


def altprice_step(message, result, minprice):
    if message.text == 'yes':
        show_result(message.chat.id, result, minprice)
    else:
        restart(message.chat.id)


def show_result(chat_id, result, price):
    for i in result:
        if i[2] <= price:
            bot.send_message(chat_id, f'{i[0]}, price {i[2]} rub, link: {i[3]}')
    restart(chat_id)


def add_to_watchlist():
    with open('watchlist.csv', 'a+', encoding='utf-8', newline='') as wl:
        writer = csv.writer(wl)
        writer.writerow(user_list)
        bot.send_message(user_list[0], f'''
                    {user_list[2]} by less then {user_list[3]} rub added to watchlist
                    Database updates every 09:00 and 23:00 (GMT+3)
                    I inform you, if something in you price range is found.
                    ''', reply_markup=yes_no_markup())
        restart(user_list[0])


def restart(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(types.KeyboardButton('/start'))
    bot.send_message(chat_id, "Restart?", reply_markup=markup)


def yes_no_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(types.KeyboardButton('yes'))
    markup.add(types.KeyboardButton('no'))
    return markup


def search_add_markup():
    # markup = types.ReplyKeyboardMarkup(row_width=2)
    # markup.add(types.KeyboardButton('search'))
    # markup.add(types.KeyboardButton('add to watchlist'))
    # markup.add(types.KeyboardButton('my watchlist'))
    markup = types.InlineKeyboardMarkup(row_width = 2)
    markup.add(types.InlineKeyboardButton('search', callback_data=0))
    markup.add(types.InlineKeyboardButton('add to watchlist', callback_data=1))
    markup.add(types.InlineKeyboardButton('my watchlist', callback_data=2))
    return markup


def watchlist_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(types.KeyboardButton('Clear all'))
    markup.add(types.KeyboardButton('restart'))
    return markup


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.infinity_polling()
