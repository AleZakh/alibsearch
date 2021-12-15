# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code for telegram-bor @alibru_search_bot.

import main
import telebot
from telebot import types
import csv
#import schedule
#import time


with open('bot_token.txt') as t:
    token = t.read()

bot = telebot.TeleBot(token, parse_mode=None)
user_dict = {}


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    msg = bot.send_message(message, """\
Hi!
Do you want to search for books or add one to a watchlist?
""", reply_markup=search_add_markup())
    bot.register_next_step_handler(msg, second_step)


def second_step(message):
    user_dict[message.chat.id] = [message.text]

#    if message.text=='my watchlist':
#        with open('watchlist.csv', 'r', encoding='utf-8') as wl:
#            reader = csv.DictReader(wl)
#            #for
#
#        msg = bot.send_message(message, """\
#        Your watchlist:
#        {}
#        """, reply_markup=watchlist_markup())
#        bot.register_next_step_handler(msg, my_watchlist())
#        return

    markup = types.ReplyKeyboardRemove(selective=False)
    msg = bot.send_message(message, """\
Input author or/and book name in russian:
""", reply_markup=markup)
    bot.register_next_step_handler(msg, name_step)


def name_step(message):
    try:
        user_dict[message.chat.id].append(message.text)
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
        user_dict[message.chat.id].append(price)
        print(user_dict[message.chat.id])

        if user_dict[message.chat.id][0]=='add to watchlist':
            add_to_watchlist()
            return

        result = main.main(user_dict[message.chat.id][1])

        if not result:
            bot.send_message(message.chat.id, f'Nothing was found on alib.ru. Try another author or/and book name')
        else:
            minprice = main.minprice(result)
            user_dict[message.chat.id].append(minprice)
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
    with open('watchlist.csv', 'a+', encoding='utf-8',newline='') as wl:
        writer = csv.writer(wl)
        for key, value in user_dict.items():
            writer.writerow([key, value])
            bot.send_message(key, f'''
                    {user_dict[key][1]} by less then {user_dict[key][2]} rub added to watchlist
                    Database updates every 09:00 and 23:00 (GMT+3)
                    I inform you, if something in you price range is found.
                    ''', reply_markup=yes_no_markup())
            restart(key)


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()


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
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(types.KeyboardButton('search'))
    markup.add(types.KeyboardButton('add to watchlist'))
    markup.add(types.KeyboardButton('my watchlist'))
    return markup


def watchlist_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(types.KeyboardButton('Clear all'))
    markup.add(types.KeyboardButton('restart'))
    return markup


bot.infinity_polling()
