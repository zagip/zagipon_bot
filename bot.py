import telebot
from telebot import types
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import random
import string
import time
import threading

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
bot = telebot.TeleBot(API_TOKEN)

my_id = bot.get_me().id

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

app = create_app()
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20))
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(200))

def generate_random_filename(extension):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + extension

ANTISPAM_MAX_MESSAGES = 6
ANTISPAM_PERIOD = 180  # 3 minutes in seconds
user_message_timestamps = {}
_antispam_lock = threading.Lock()

def is_rate_limited(user_id):
    now = time.time()
    with _antispam_lock:
        timestamps = user_message_timestamps.get(user_id, [])
        timestamps = [t for t in timestamps if now - t < ANTISPAM_PERIOD]
        user_message_timestamps[user_id] = timestamps
        if len(timestamps) >= ANTISPAM_MAX_MESSAGES:
            return True
        timestamps.append(now)
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! \nЭто - бот предложки https://t.me/+OtxxYjLgRP00NzVi. \n\nВы можете отправлять мне сообщения с текстом или любым медиа.")

@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
    'text', 'location', 'contact', 'sticker', 'animation', 'poll'])
def uzhimatel(message):
    if message.chat.id == GROUP_ID and message.from_user.id != my_id:
        bot.delete_message(GROUP_ID, message.id)
        return

    if is_rate_limited(message.from_user.id):
        bot.send_message(message.chat.id, "Слишком много сообщений! Подождите немного перед отправкой нового.")
        return

    user_info = f"Отправитель: {message.from_user.first_name} (@{message.from_user.username})"
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "+user_info)
    mid = bot.forward_message(GROUP_ID, message.chat.id, message.id).id

    markup = types.InlineKeyboardMarkup()
    btn_send = types.InlineKeyboardButton("Указать имя", callback_data=json.dumps({"a": 0, "c":message.chat.id, "m":message.id, "i": mid}))
    btn_cancel = types.InlineKeyboardButton("Не указывать", callback_data=json.dumps({"a": 1, "c":message.chat.id, "m":message.id, "i": mid}))
    markup.add(btn_send, btn_cancel)

    bot.send_message(message.chat.id, "Указывать ли имя при отправке в канал?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    with app.app_context():
        d = json.loads(call.data)
        if "send" in d:
            if d["send"]==1:
                if d["a"]==0:
                    message = bot.forward_message(CHANNEL_ID, d["c"], d["m"])
                    content_type = message.content_type
                else:
                    bot.copy_message(CHANNEL_ID, d["c"], d["m"])

                    message = bot.forward_message(GROUP_ID, d["c"], d["m"])
                    content_type = message.content_type
                    bot.delete_message(GROUP_ID, message.id)

                bot.delete_message(GROUP_ID, call.message.id)
                bot.send_message(GROUP_ID, f"Сообщение отправлено (by {call.from_user.first_name} @{call.from_user.username})", reply_to_message_id=d["i"])
                bot.send_message(d["c"], "Сообщение отправлено", reply_to_message_id=d["m"])

                file_path = None
                if content_type in ['photo', 'video']:
                    file_info = bot.get_file(message.photo[-1].file_id if content_type == 'photo' else message.video.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    extension = os.path.splitext(file_info.file_path)[1]
                    random_filename = generate_random_filename(extension)
                    file_path = f"static/{random_filename}"
                    with open(file_path, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    file_path = random_filename

                new_post = Post(
                    content_type=content_type,
                    text=message.caption if content_type in ['photo', 'video'] else message.text,
                    file_path=file_path
                )
                db.session.add(new_post)
                db.session.commit()
            else:
                bot.delete_message(GROUP_ID, call.message.id)
                bot.send_message(GROUP_ID, f"Сообщение отклонено (by {call.from_user.first_name} @{call.from_user.username})", reply_to_message_id=d["i"])
                bot.send_message(d["c"], "Сообщение отклонено", reply_to_message_id=d["m"])
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(d["c"], "Спасибо за контент! Отправил загипычам на модерацию =)")
            markup = types.InlineKeyboardMarkup()
            btn_send = types.InlineKeyboardButton("Отправить", callback_data=json.dumps({"send": 1, "a":d["a"], "c":d["c"], "m":d["m"], "i":d["i"]}))
            btn_nonanon = types.InlineKeyboardButton("Отправить (non-anon)", callback_data=json.dumps({"send": 1, "a":0, "c":d["c"], "m":d["m"], "i":d["i"]}))
            btn_cancel = types.InlineKeyboardButton("Не отправлять", callback_data=json.dumps({"send": 0, "a":d["a"], "c":d["c"], "m":d["m"], "i":d["i"]}))
            markup.add(btn_send, btn_nonanon, btn_cancel)
            
            bot.send_message(GROUP_ID, f"Отправить в канал? (anon={d['a']}, nick={call.from_user.username}, username={call.from_user.first_name} {call.from_user.last_name})", reply_markup=markup, reply_to_message_id=d["i"])

@bot.message_handler(commands=['stop_bot'])
def stop_bot(message):
    if message.chat.id == GROUP_ID:
        bot.stop_polling()
        bot.send_message(message.chat.id, "Бот остановлен")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        bot.polling(non_stop=True)
