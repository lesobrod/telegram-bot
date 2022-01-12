import telebot
import json
from requests import request
from random import choice
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

'''
Тестовый бот. Выполняет команды 
/help:
/get_data
/gotourl
/exit: завершение работы бота

Любое другое введенное сообщение переводит на случайный (из списка)
язык с помощью Rakuten Rapid API - Microsoft Translator
'''

TEST_BOT_NAME = 'TestingTestBotoBot'
TEST_TOKEN = '5012013004:AAEynUWNGzNNvjV-X7Lnvi744YNDp4ZRadA'
LANGUAGES = ['ba', 'bg', 'uk', 'uz', 'fr']

bot = telebot.TeleBot(TEST_TOKEN, parse_mode='HTML')

API_DETECT_URL = "https://microsoft-translator-text.p.rapidapi.com/Detect"

API_TRANSLATE_URL = "https://microsoft-translator-text.p.rapidapi.com/translate"
api_detect_headers = {
    'content-type': "application/json",
    'x-rapidapi-key': "2421d88313mshfabf818b1b8af85p1e2c18jsnf54c16d3cf46",
    'x-rapidapi-host': "microsoft-translator-text.p.rapidapi.com"
}
api_translate_headers = headers = {
    'content-type': "application/json",
    'x-rapidapi-key': "2421d88313mshfabf818b1b8af85p1e2c18jsnf54c16d3cf46",
    'x-rapidapi-host': "microsoft-translator-text.p.rapidapi.com"
}

# Стационарная клава
keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
row = [KeyboardButton(text="> Help"), KeyboardButton(text="> Get data")]
keyboard.add(*row)
row = [KeyboardButton(text="> Go to URL"), KeyboardButton(text="> Exit")]
keyboard.add(*row)


# Обработка нажатий клавиш
@bot.message_handler(func=lambda message: message.text.startswith('>'))
def keyboard_handler(message):
    if 'Exit' in message.text:
        bot.stop_bot()

    elif 'Help' in message.text:
        bot.send_message(message.from_user.id, "Done with Keyboard", reply_markup=keyboard)
    elif 'URL' in message.text:

        ...
    else:
        ...


# Обработка идет в порядке записи функций здесь!
@bot.message_handler(content_types=["text"])
# Реакция на сообщения
def text_messages_handler(message):
    print(message.text)
    spam = json.dumps([{"Text": message.text}])
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
    egg = response.json()
    print(egg)
    # reply_to: ответ с цитатой, bot.send_message(message.chat.id - просто
    bot.send_message(message.chat.id, egg[0]["translations"][0]["text"])


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f'Unexpected error: {e}')
