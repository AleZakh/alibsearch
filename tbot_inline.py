# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code for telegram-bor @alibru_search_bot.


import logging
from threading import Thread
import time
import os

import schedule
from flask import Flask, request
import telebot
from telebot import types
import redis

import alib_search

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

token = os.environ['token']
r = redis.from_url(os.environ.get("REDIS_URL"))
logging.info(f'!!!redis ping: {r.ping()}')
bot = telebot.TeleBot(token)

server = Flask(__name__)
logging.debug(server)

user_dict = {}
user_result = []


# Bot functions

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    logging.info(call.data)
    if call.data in ['search', 'add_wl']:
        first_question(call)
    if call.data == 'show_wl':
        show_watchlist(call.from_user.id)
    if call.data == 'clear':
        clear_watchlist(call.from_user.id)
    if call.data == 'yes':
        show_result(0, call.from_user.id)
    if call.data == 'return':
        return_to_start(call.from_user.id)
    try:
        show_result(int(call.data), call.from_user.id)
    except Exception as e:
        logging.info(e)


@bot.message_handler(func=lambda message: True)
def send_welcome(message):
    user_dict[message.chat.id] = {}
    user_dict[message.chat.id]['chat_id'] = message.chat.id
    logging.info(user_dict)
    msg = bot.reply_to(message, """\
Hi!
Do you want to search for books or add one to a watchlist?
""", reply_markup=search_add_markup())
    user_dict[message.chat.id]['1st_message_id'] = msg.message_id


def first_question(call):
    user_dict[call.from_user.id]['call'] = call.data
    logging.info(user_dict)
    if call.data == "search" or call.data == "add_wl":
        msg = bot.send_message(user_dict[call.from_user.id]['chat_id'], 'Input author or/and book name:')
        user_dict[call.from_user.id]['last_message_id'] = msg.message_id
        bot.register_next_step_handler(msg, price_step)


def price_step(message):
    try:
        user_dict[message.chat.id]['query'] = message.text
        logging.info(user_dict)
        msg = bot.reply_to(message, 'Max price?')
        user_dict[message.chat.id]['last_message_id'] = msg.message_id
        bot.register_next_step_handler(msg, result_step)
    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again", reply_markup=return_markup())


def result_step(message):
    try:
        if not message.text.isdigit():
            msg = bot.reply_to(message, 'Price should be a number. So... max price?')
            user_dict[message.chat.id]['last_message_id'] = msg.message_id
            bot.register_next_step_handler(msg, result_step)
            return

        user_dict[message.chat.id]['price'] = int(message.text)
        logging.info(user_dict)

        if user_dict[message.chat.id]['call'] == 'add_wl':
            add_to_watchlist(message)

        if user_dict[message.chat.id]['call'] == 'search':
            search_result(message)

    except Exception as e:
        logging.info(e)
        bot.reply_to(message, "oooops, something went wrong. Let's try again", reply_markup=return_markup())


def add_to_watchlist(msg):
    r.rpush(user_dict[msg.chat.id]["chat_id"], user_dict[msg.chat.id]["query"], user_dict[msg.chat.id]["price"])
    msg = bot.send_message(user_dict[msg.chat.id]["chat_id"], f''' 
            ✍🏻 {user_dict[msg.chat.id]["query"]} by less then {user_dict[msg.chat.id]["price"]} rub added to watchlist
            - Database updates every 09:00 and 23:00 (GMT+3)
            - I inform you, if something in you price range is found.
                    ''', reply_markup=return_markup())
    user_dict[msg.chat.id]['last_message_id'] = msg.message_id
    logging.info(f'!!!redis test get command: {r.lrange(msg.chat.id, 0, r.llen(msg.chat.id))}')


def search_result(msg):
    user_result.clear()
    bot.send_message(user_dict[msg.chat.id]['chat_id'], 'looking for it...')
    bot.send_chat_action(user_dict[msg.chat.id]['chat_id'], 'typing')

    user_list = alib_search.main(user_dict[msg.chat.id]['query'])
    logging.info(user_list)
    if not user_list:
        msg = bot.send_message(user_dict[msg.chat.id]['chat_id'],
                               f'Nothing was found on alib.ru. Try another author or/and book name')
        user_dict[msg.chat.id]['last_message_id'] = msg.message_id
        bot.register_next_step_handler(msg, price_step)

    else:
        user_dict[msg.chat.id]['min_price'] = alib_search.minprice(user_list)
        logging.info(user_dict)
        if user_dict[msg.chat.id]['min_price'] > user_dict[msg.chat.id]['price']:
            user_result.extend(list(filter(lambda c: c[:][2] <= user_dict[msg.chat.id]['min_price'], user_list)))
            msg = bot.send_message(user_dict[msg.chat.id]['chat_id'], f'''
            Nothing was found in your price range (<{user_dict[msg.chat.id]['price']} руб)
            Minimal price is {user_dict[msg.chat.id]['min_price']}.
            Show minimal price positions?
            ''', reply_markup=yes_no_markup())
            user_dict[msg.chat.id]['last_message_id'] = msg.message_id
            user_result.extend(list(filter(lambda c: c[:][2] <= user_dict[msg.chat.id]['min_price'], user_list)))
            user_dict[msg.chat.id]['result_pages'] = len(user_result) // 5 if len(user_result) % 5 == 0 \
                else len(user_result) // 5 + 1

        else:
            user_result.extend(list(filter(lambda c: c[:][2] <= user_dict[msg.chat.id]['price'], user_list)))
            user_dict[msg.chat.id]['result_pages'] = len(user_result) // 5 if len(user_result) % 5 == 0 \
                else len(user_result) // 5 + 1
            show_result(0, msg.chat.id)


def show_result(page_number, chat_id):
    logging.info(page_number)
    result_message_text = ''

    for i in user_result[
             page_number * 5:page_number * 5 + 5 if page_number * 5 + 5 <= len(user_result) - 1 else len(user_result)]:
        name = telegram_parser_format(i[0])
        price = i[2]
        link = i[3]
        result_message_text += f'📔 {name}, price *{price}* rub, [link]({link}) \n \n '
    if 'is_result_msg' in user_dict[chat_id].keys():
        bot.edit_message_text(result_message_text,
                              message_id=user_dict[chat_id]['last_message_id'],
                              chat_id=chat_id,
                              parse_mode='MarkdownV2',
                              disable_web_page_preview=True,
                              reply_markup=result_markup(page_number, chat_id))
    else:
        result_message = bot.send_message(chat_id,
                                          text=result_message_text,
                                          parse_mode='MarkdownV2',
                                          disable_web_page_preview=True,
                                          reply_markup=result_markup(page_number, chat_id))
        user_dict[chat_id]['last_message_id'] = result_message.message_id
        user_dict[chat_id]['is_result_msg'] = True
        logging.info(user_dict)


def show_watchlist(chat_id):
    wl_msg_text = ''
    for i in range(0, r.llen(chat_id), 2):
        wl_msg_text += f'📔 {r.lindex(chat_id, i).decode("utf-8")},' \
                       f' price *<{r.lindex(chat_id, i + 1).decode("utf-8")}* rub \n \n '
    if len(wl_msg_text) > 0:
        msg = bot.send_message(chat_id,
                               text='Your watchlist: \n \n' + wl_msg_text,
                               parse_mode='MarkdownV2',
                               disable_web_page_preview=True,
                               reply_markup=watchlist_markup())

    else:
        msg = bot.send_message(chat_id,
                               text='Your watchlist is empty',
                               reply_markup=return_markup())
    user_dict[chat_id]['last_message_id'] = msg.message_id


def clear_watchlist(chat_id):
    r.delete(chat_id)
    msg = bot.send_message(chat_id,
                           text='Your watchlist is cleared',
                           reply_markup=return_markup())
    user_dict[chat_id]['last_message_id'] = msg.message_id


def return_to_start(chat_id):
    i = user_dict[chat_id]['1st_message_id'] + 1
    while i <= user_dict[chat_id]['last_message_id'] + 1:
        try:
            bot.delete_message(chat_id=user_dict[chat_id]['chat_id'], message_id=i)
            i += 1
        except:
            i += 1

    if 'is_result_msg' in user_dict[chat_id].keys():
        user_dict[chat_id].pop('is_result_msg')
    user_dict[chat_id].pop('last_message_id')
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
    markup.row(types.InlineKeyboardButton('clear all', callback_data='clear'),
               types.InlineKeyboardButton('return', callback_data='return'))
    return markup


def result_markup(cur_page, chat_id):
    logging.info(str(cur_page) + ' of ' + str(user_dict[chat_id]['result_pages'] - 1))
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton('1<<', callback_data='0') if cur_page >= 2
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'{cur_page}<', callback_data=str(cur_page - 1)) if cur_page > 0
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'>{cur_page + 2}', callback_data=cur_page + 1)
               if cur_page < user_dict[chat_id]['result_pages'] - 1
               else types.InlineKeyboardButton('-', callback_data=' '),
               types.InlineKeyboardButton(f'>>{user_dict[chat_id]["result_pages"]}',
                                          callback_data=user_dict[chat_id]["result_pages"] - 1)
               if cur_page < user_dict[chat_id]['result_pages'] - 1
               else types.InlineKeyboardButton('-', callback_data=' '))
    markup.row(types.InlineKeyboardButton('return', callback_data='return'))

    return markup


def return_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton('return', callback_data='return'))

    return markup


def telegram_parser_format(txt):
    reserved_sym = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for i in reserved_sym:
        txt = txt.replace(i, '\\' + i)
    return txt


def watchlist_search():
    user_result.clear()
    watchlist = []
    for chat_id in r.keys():
        for i in range(0, r.llen(chat_id), 2):
            watchlist.append([r.lindex(chat_id, i).decode('utf-8'), r.lindex(chat_id, i + 1).decode('utf-8')])
    try:
        for row in watchlist:
            user_list = (list(filter(lambda c: c[:][2] <= int(row[1]), alib_search.main(row[0]))))
            logging.info('!!!!!!!!!!!!!')
            logging.info(user_list)
            logging.info('!!!!!!!!!!!!!')
            if len(user_list) > 0:
                msg = bot.send_message(row[0], 'Your watchlist query was found!')
                user_dict[row[0]]['last_message_id'] = msg.message_id
                user_dict[row[0]]['1st_message_id'] = msg.message_id
                user_result.extend(user_list)
                user_dict[row[0]]['result_pages'] = len(user_result) // 5 if len(user_result) % 5 == 0 \
                    else len(user_result) // 5 + 1
                show_result(0, row[0])
    except Exception as e:
        logging.info(e)


def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(60)


# Server side

@server.route('/' + token, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    server.logger.info(update)

    return "!", 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://alibru-search-bot.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    schedule.every(10).minutes.do(watchlist_search)

#    schedule.every().day.at("23:00").do(watchlist_search)
#    schedule.every().day.at("08:00").do(watchlist_search)
    Thread(target=schedule_checker).start()

    server.debug = True
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 80)))
