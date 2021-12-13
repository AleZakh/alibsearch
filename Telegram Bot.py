# !/usr/bin/env python3
import main
import telebot

bot = telebot.TeleBot('5016356128:AAFbLEBBdyT2Y1Lfx5nNnJJiR8GuusWGW5I', parse_mode=None)
user_dict = {}

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
Hi!
Input author or/and book name in russian:
""")
    bot.register_next_step_handler(msg, name_step)


def name_step(message):
    try:
        user_dict[message.chat.id] = [message.text]
        msg = bot.reply_to(message, 'Max price?')
        bot.register_next_step_handler(msg, price_step)
    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again")
    #    send_welcome('start')

def price_step(message):
    try:
        if not message.text.isdigit():
            msg = bot.reply_to(message, 'Price should be a number. So... max price?')
            bot.register_next_step_handler(msg, price_step)
            return
        price = int(message.text)
        user_dict[message.chat.id].append(price)
        print (user_dict[message.chat.id])
        result = main.main(user_dict[message.chat.id][0])
        for i in result:
            if i[2] < price:
                bot.send_message(message.chat.id, f'{i[0]}, price {i[2]} rub, link: {i[3]}')
    except:
        bot.reply_to(message, "oooops, something went wrong. Let's try again")
    #    send_welcome('start')


bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

bot.infinity_polling()
