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
    bot.send_message(message.chat.id, "Привет! Вы можете отправлять мне сообщения с текстом, видео и фото.")

@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
    'text', 'location', 'contact', 'sticker', 'animation', 'poll'])
def uzhimatel(message):
    if message.chat.id == GROUP_ID and message.from_user.id != my_id:
        bot.delete_message(GROUP_ID, message.id)
        return


    print("MASSIVE")
    user_info = f"Отправитель: {message.from_user.first_name} (@{message.from_user.username})"
    mid = bot.send_message(GROUP_ID, user_info).id

    markup = types.InlineKeyboardMarkup()
    btn_send = types.InlineKeyboardButton("Отправить", callback_data=json.dumps({"send": 1, "mid": mid, "ochat":message.chat.id, "omsg":message.id}))
    btn_cancel = types.InlineKeyboardButton("Не отправлять", callback_data=json.dumps({"send": 0, "mid": mid, "ochat":message.chat.id, "omsg":message.id}))
    markup.add(btn_send, btn_cancel)

    bot.copy_message(GROUP_ID, message.chat.id, message.id, reply_markup=markup)



@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    d = json.loads(call.data)
    if d["send"]:
        bot.copy_message(CHANNEL_ID, call.message.chat.id, call.message.id, reply_markup=None)
        
        bot.delete_message(GROUP_ID, call.message.id)
        bot.delete_message(GROUP_ID, d["mid"])
        bot.send_message(d["ochat"], "Сообщение отправлено", reply_to_message_id=d["omsg"])

    else:
        bot.delete_message(GROUP_ID, call.message.id)
        bot.delete_message(GROUP_ID, d["mid"])
        bot.send_message(d["ochat"], "Сообщение отклонено", reply_to_message_id=d["omsg"])




bot.polling(non_stop=True)
