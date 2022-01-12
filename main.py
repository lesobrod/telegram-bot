import config
import telebot
from telebot.types import Message, CallbackQuery
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from my_redis import redis_db

bot = telebot.TeleBot(config.TOKEN, parse_mode='HTML')


def make_message(key: str) -> str:
    """
    Takes text in config dictionary with key
    :param key: str key
    :return: text of message from config.MESSAGE_DICT
    """
    return config.MESSAGE_DICT[key]


@bot.message_handler(commands=['help', 'start'])
def get_command_start_help(message: Message) -> None:
    """
    "/help" and "/start" command handler
    :param message: Message
    :return: None
    """
    if 'start' in message.text:
        bot.send_message(message.chat.id, make_message('hello'))
    else:
        bot.send_message(message.chat.id, make_message('help'))


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f'Unexpected error: {e}')
