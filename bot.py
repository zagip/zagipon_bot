import telebot
from telebot import types

API_TOKEN = '7983118789:AAE_oZyr-JhlK6DyaotZ4LS-P1jtFv5j980'
bot = telebot.TeleBot(API_TOKEN)

GROUP_ID = -4716889464
CHANNEL_ID = -1002377166835
#CHANNEL_ID = -1002385851046

@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_content(message):
    markup = types.InlineKeyboardMarkup()
    btn_send = types.InlineKeyboardButton("Отправить", callback_data='send')
    btn_cancel = types.InlineKeyboardButton("Не отправлять", callback_data='cancel')
    markup.add(btn_send, btn_cancel)
    
    if message.content_type == 'text':
        bot.send_message(GROUP_ID, message.text, reply_markup=markup)
    elif message.content_type in ['photo', 'video']:
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            bot.send_photo(GROUP_ID, photo_id, caption=message.caption, reply_markup=markup)
        elif message.content_type == 'video':
            video_id = message.video.file_id
            bot.send_video(GROUP_ID, video_id, caption=message.caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == 'send':
        if call.message.content_type == 'text':
            bot.send_message(CHANNEL_ID, call.message.text)
        elif call.message.content_type == 'photo':
            photo_id = call.message.photo[-1].file_id
            bot.send_photo(CHANNEL_ID, photo_id, caption=call.message.caption)
        elif call.message.content_type == 'video':
            video_id = call.message.video.file_id
            bot.send_video(CHANNEL_ID, video_id, caption=call.message.caption)

        bot.send_message(GROUP_ID, "Контент отправлен", reply_to_message_id=call.message.message_id)
    elif call.data == 'cancel':
        bot.send_message(GROUP_ID, "Отправка отменена", reply_to_message_id=call.message.message_id)


bot.polling(non_stop=True)