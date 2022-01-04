# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code for telegram-bor @alibru_search_bot.

import main
import telebot
from telebot import types
# import csv
import logging

# import sys
# import schedule
# import time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open('bot_token.txt') as t:
    token = t.read()
user_dict = {}
user_result = []

bot = telebot.TeleBot(token, parse_mode=None)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    logging.info(call.data)
    if call.data in ['search', 'add_wl', 'show_wl']:
        first_question(call)
    if call.data == 'yes':
        show_result(0)
    if call.data == 'return':
        return_to_start()
    try:
        show_result(int(call.data))
    except Exception as e:
        logging.info(e)


@bot.message_handler(func=lambda message: True)
def send_welcome(message):
    user_dict['chat_id'] = message.chat.id
    logging.info(user_dict)
    bot.reply_to(message, """\
Hi!
Do you want to search for books or add one to a watchlist?
""", reply_markup=search_add_markup())


def first_question(call):
    user_dict['1st_message_id'] = call.message.message_id
    user_dict['call'] = call.data
    logging.info(user_dict)
    if call.data == "search" or call.data == "add_wl":
        msg = bot.send_message(user_dict['chat_id'], 'Input author or/and book name:')
        user_dict['last_message_id'] = msg.message_id
        bot.register_next_step_handler(msg, price_step)
    elif call.data == "show_wl":
        bot.edit_message_text("You chose: " + user_dict['chat_id'], user_dict['1st_message_id'] + 1,
                              reply_markup=search_add_markup())

def price_step(message):
    try:
        user_dict['query'] = message.text
        logging.info(user_dict)
        msg = bot.reply_to(message, 'Max price?')
        user_dict['last_message_id'] = msg.message_id
        bot.register_next_step_handler(msg, result_step)
    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again")


def result_step(message):
    try:

        if not message.text.isdigit():
            msg = bot.reply_to(message, 'Price should be a number. So... max price?')
            user_dict['last_message_id'] = msg.message_id
            bot.register_next_step_handler(msg, result_step)
            return

        bot.send_message(message.chat.id, 'looking for it...')
        bot.send_chat_action(message.chat.id, 'typing')

        user_dict['price'] = int(message.text)
        logging.info(user_dict)

        # if user_list[1] == 'add to watchlist':
        #     add_to_watchlist()
        #     return

        user_list = main.main(user_dict['query'])
        logging.info(user_list)
        if not user_list:
            msg=bot.send_message(message.chat.id, f'Nothing was found on alib.ru. Try another author or/and book name')
            user_dict['last_message_id'] = msg.message_id
            bot.register_next_step_handler(msg, price_step)

        else:
            user_dict['min_price'] = main.minprice(user_list)
            logging.info(user_dict)
            if user_dict['min_price'] > user_dict['price']:
                user_result.extend(list(filter(lambda c: c[:][2] <= user_dict['min_price'], user_list)))
                msg=bot.send_message(user_dict['chat_id'], f'''
                Nothing was found in your price range (<{user_dict['price']} руб)
                Minimal price is {user_dict['min_price']}.
                Show minimal price positions?
                ''', reply_markup=yes_no_markup())
                user_dict['last_message_id'] = msg.message_id
                user_result.extend(list(filter(lambda c: c[:][2] <= user_dict['min_price'], user_list)))
                user_dict['result_pages'] = len(user_result) // 5 if len(user_result) % 5 == 0 \
                    else len(user_result) // 5 + 1

            else:

                user_result.extend(list(filter(lambda c: c[:][2] <= user_dict['price'], user_list)))
                user_dict['result_pages'] = len(user_result) // 5 if len(user_result) % 5 == 0 \
                    else len(user_result) // 5 + 1
                show_result(0)

    except Exception as e:
        logging.info(e)
        bot.reply_to(message, "oooops, something went wrong. Let's try again")
    #     # restart(message.chat.id)


def show_result(page_number):
    logging.info(page_number)
    result_message_text = ''
    i = page_number * 5
    while i != page_number * 5 + 5 and i <= len(user_result) - 1:
        name = telegram_parser_format(user_result[i][0])
        price = user_result[i][2]
        link = user_result[i][3]
        result_message_text += u'📔' + f' {name}, price *{price}* rub, [link]({link}) \n \n '
        i = i + 1
    if 'result_message_id' in user_dict.keys():
        bot.edit_message_text(result_message_text,
                              message_id=user_dict['result_message_id'],
                              chat_id=user_dict['chat_id'],
                              parse_mode='MarkdownV2',
                              disable_web_page_preview=True,
                              reply_markup=result_markup(page_number))
    else:
        result_message = bot.send_message(user_dict['chat_id'],
                                          text=result_message_text,
                                          parse_mode='MarkdownV2',
                                          disable_web_page_preview=True,
                                          reply_markup=result_markup(page_number))
        user_dict['last_message_id'] = result_message.message_id
        logging.info(user_dict)



def return_to_start():
    i=user_dict['1st_message_id']+1
    while i<=user_dict['last_message_id']+1:
        try:
            bot.delete_message(chat_id=user_dict['chat_id'], message_id=i)
            i+=1
        except:
            i += 1

    user_dict.pop('last_message_id')
    user_result.clear()

def search_add_markup():
    markup = types.InlineKeyboardMarkup(row_width=5)
    markup.row(types.InlineKeyboardButton('search', callback_data='search'))
    markup.row(types.InlineKeyboardButton('add to watchlist', callback_data='add_wl'),
               types.InlineKeyboardButton('show my watchlist', callback_data='show_wl'))
    return markup


def yes_no_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('yes', callback_data='yes'),
               types.InlineKeyboardButton('no', callback_data='return'))
    return markup


def watchlist_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('clear all', callback_data='clear'))
    markup.add(types.InlineKeyboardButton('return', callback_data='return'))
    return markup


def result_markup(cur_page):
    logging.info(str(cur_page) + ' of ' + str(user_dict['result_pages'] - 1))
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton('1<<', callback_data='0') if cur_page >= 2
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'{cur_page}<', callback_data=str(cur_page - 1)) if cur_page > 0
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'>{cur_page + 2}', callback_data=cur_page + 1)
               if cur_page < user_dict['result_pages'] - 1
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'>>{user_dict["result_pages"]}', callback_data=user_dict["result_pages"] - 1)
               if cur_page < user_dict['result_pages'] - 1
               else types.InlineKeyboardButton('-', callback_data=' '))
    markup.row(types.InlineKeyboardButton('return', callback_data='return'))

    return markup


def telegram_parser_format(txt):
    reserved_sym = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for i in reserved_sym:
        txt = txt.replace(i, '\\' + i)
    return txt


bot.infinity_polling()
