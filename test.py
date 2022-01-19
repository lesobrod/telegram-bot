import telebot
import json
from test_config import *
from requests import request
from random import choice
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

'''
Тестовый бот. Выполняет команды 
/help: Показывает стандартное сообщение
/get_data: Тест вывода картинки
/gotourl: Предлагает на выбор три варианта перехода на другие сайты
/exit: завершение работы бота  

Любое другое введенное сообщение переводит на случайный (из списка)
язык с помощью Rakuten Rapid API - Microsoft Translator
'''
# TODO завершение работы бота -- уточнить в каком смысле

bot = telebot.TeleBot(TEST_TOKEN, parse_mode='HTML')


def translate_text(user_text):
    print(user_text)
    spam = json.dumps([{"Text": user_text}])
    response = request("POST", API_DETECT_URL,
                       data=spam, headers=api_detect_headers,
                       params={"api-version": "3.0"})
    egg = response.json()
    print(egg)
    lang_from = egg[0]["language"]
    lang_to = choice(LANGUAGES)

    querystring = {"to": lang_to, "api-version": "3.0", "from": lang_from,
                   "profanityAction": "NoAction", "textType": "plain"}
    response = request("POST", API_TRANSLATE_URL,
                       data=spam, headers=api_translate_headers,
                       params=querystring)
    return response.json()[0]["translations"][0]["text"]


# Стационарная клава
keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
row = [KeyboardButton(text="Help"), KeyboardButton(text="Get data")]
keyboard.add(*row)
row = [KeyboardButton(text="Go to URL"), KeyboardButton(text="Exit")]
keyboard.add(*row)


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    print('1')
    bot.send_message(message.chat.id, START_MESSAGE, reply_markup=keyboard)


# Показать клавиатуру
@bot.message_handler(commands=['button'])
def button_message(message):
    bot.send_message(message.chat.id, 'Выберите что вам надо', reply_markup=keyboard)


@bot.message_handler(content_types='text')
def button_handler(message):
    if 'Exit' in message.text:
        bot.stop_bot()
    elif 'Help' in message.text:
        # Есть еще from_user.id
        bot.send_message(message.chat.id, HELP_MESSAGE, reply_markup=keyboard)

    elif 'URL' in message.text:
        in_keyboard = InlineKeyboardMarkup()
        in_keyboard.row(
            InlineKeyboardButton('1', url="https://thispersondoesnotexist.com/")
        )
        in_keyboard.row(
            InlineKeyboardButton('2', url="https://picsum.photos/200"),
            InlineKeyboardButton('3', url="https://thiscatdoesnotexist.com/")
        )
        bot.send_message(message.chat.id, 'Куда пойдем?', reply_markup=in_keyboard)

    elif 'data' in message.text:
        bot.send_photo(chat_id=message.chat.id, photo='https://telegram.org/img/t_logo.png')

    else:
        # reply_to: ответ с цитатой, bot.send_message(message.chat.id - просто
        bot.send_message(message.chat.id, translate_text(message.text), reply_markup=keyboard)


print('3')
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f'Unexpected error: {e}')
