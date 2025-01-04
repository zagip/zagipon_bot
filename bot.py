import telebot
from telebot import types
import json

API_TOKEN = '7983118789:AAE_oZyr-JhlK6DyaotZ4LS-P1jtFv5j980'
bot = telebot.TeleBot(API_TOKEN)

GROUP_ID = -1002485954656
CHANNEL_ID = -1002377166835
my_id = bot.get_me().id

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Вы можете отправлять мне сообщения с текстом или любым медиа.")

@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
    'text', 'location', 'contact', 'sticker', 'animation', 'poll'])
def uzhimatel(message):
    if message.chat.id == GROUP_ID and message.from_user.id != my_id:
        bot.delete_message(GROUP_ID, message.id)
        return

    user_info = f"Отправитель: {message.from_user.first_name} (@{message.from_user.username})"
    print('[#] '+user_info)
    mid = bot.forward_message(GROUP_ID, message.chat.id, message.id).id

    markup = types.InlineKeyboardMarkup()
    btn_send = types.InlineKeyboardButton("Указать имя", callback_data=json.dumps({"a": 0, "c":message.chat.id, "m":message.id, "i": mid}))
    btn_cancel = types.InlineKeyboardButton("Не указывать", callback_data=json.dumps({"a": 1, "c":message.chat.id, "m":message.id, "i": mid}))
    markup.add(btn_send, btn_cancel)

    bot.send_message(message.chat.id, "Указывать ли имя при отправке в канал?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    d = json.loads(call.data)
    if "send" in d:
        if d["send"]==1:
            if d["a"]==0:
                bot.forward_message(CHANNEL_ID, d["c"], d["m"])
            else:
                bot.copy_message(CHANNEL_ID, d["c"], d["m"])
            bot.delete_message(GROUP_ID, call.message.id)
            bot.send_message(d["c"], "Сообщение отправлено", reply_to_message_id=d["m"])
        else:
            bot.delete_message(GROUP_ID, call.message.id)
            bot.send_message(d["c"], "Сообщение отклонено", reply_to_message_id=d["m"])
    else:
        bot.send_message(d["c"], "Спасибо за контент! Отправил загипычам на модерацию =)")
        markup = types.InlineKeyboardMarkup()
        btn_send = types.InlineKeyboardButton("Отправить", callback_data=json.dumps({"send": 1, "c":d["c"], "m":d["m"], "a":d["a"]}))
        btn_cancel = types.InlineKeyboardButton("Не отправлять", callback_data=json.dumps({"send": 0, "c":d["c"], "m":d["m"], "a":d["a"]}))
        markup.add(btn_send, btn_cancel)
        
        bot.send_message(GROUP_ID, f"Отправить в канал? (anon={d['a']})", reply_markup=markup)

bot.polling(non_stop=True)
