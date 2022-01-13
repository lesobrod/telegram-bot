import os
from my_redis import redis_db
import config
import telebot
from loguru import logger
from telebot.types import Message, CallbackQuery
from telebot.types import ReplyKeyboardMarkup, \
    InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from Botrequests.hotels import get_hotels
from Botrequests.locations import exact_location, make_locations_list
from utils import is_input_correct, get_parameters_information, \
    make_message, steps, answer, \
    is_user_in_db, add_user, extract_search_parameters

logger.configure(**config.LOGGER_CONFIG)

# BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(config.TOKEN, parse_mode='HTML')


@bot.message_handler(commands=['help', 'start'])
def get_command_help(message: Message) -> None:
    """
    "/help" command handler, displays information about bot commands in the chat
    :param message: message
    :return: none
    """
    if not is_user_in_db(message):
        add_user(message)
    if 'start' in message.text:
        logger.info(f'"start" command is called')
        bot.send_message(message.chat.id, answer('hello', message))
    else:
        logger.info(f'"help" command is called')
        bot.send_message(message.chat.id, answer('help', message))


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def get_searching_commands(message: Message) -> None:
    """
    Обработка основных команд
    :param message: Message
    :return: None
    """
    logger.info("\n" + "=" * 100 + "\n")
    if not is_user_in_db(message):
        add_user(message)

    chat_id = message.chat.id
    # Если команда поступила state = 1
    redis_db.hset(chat_id, 'state', 1)

    if 'lowprice' in message.text:
        redis_db.hset(chat_id, 'order', 'PRICE')
        logger.info('"lowprice" command is called')
    elif 'highprice' in message.text:
        redis_db.hset(chat_id, 'order', 'PRICE_HIGHEST_FIRST')
        logger.info('"highprice" command is called')
    else:
        redis_db.hset(chat_id, 'order', 'DISTANCE_FROM_LANDMARK')
        logger.info('"bestdeal" command is called')
    logger.info(redis_db.hget(chat_id, 'order'))
    state = redis_db.hget(chat_id, 'state')
    logger.info(f"Current state: {state}")
    print(state)
    bot.send_message(chat_id, make_message(message, 'question_'))


@bot.message_handler(commands=['history'])
# TODO сделать
def get_command_history(message: Message) -> None:
    """
    обработка команды /history
    :param message: message
    :return: none
    """
    if not is_user_in_db(message):
        add_user(message)
    logger.info(f'{get_command_history.__name__} called with {message}')
    ...


def get_locations(msg: Message) -> None:
    """
    Поиск отелей в городе
    :param msg: message
    :return: none
    """
    if not is_input_correct(msg):
        bot.send_message(msg.chat.id, make_message(msg, 'mistake_'))
    else:
        # Предупрежд об ожидании
        wait_msg = bot.send_message(msg.chat.id, answer('wait', msg))

        # Вызывается make_locations_list из locations
        locations = make_locations_list(msg)

        bot.delete_message(msg.chat.id, wait_msg.id)

        if not locations or len(locations) < 1:
            bot.send_message(msg.chat.id, answer('locations_not_found', msg))
        elif locations.get('bad_request'):
            bot.send_message(msg.chat.id, answer('bad_request', msg))
        else:
            menu = InlineKeyboardMarkup()
            print('get_loc')

            for loc_name, loc_id in locations.items():
                print(type(loc_name), type(loc_id))
                menu.add(InlineKeyboardButton(text=loc_name,
                                              callback_data='code' + loc_id))

            menu.add(InlineKeyboardButton(text='cancel', callback_data='cancel'))

            bot.send_message(msg.chat.id, 'aaa', reply_markup=menu)


def image_list(msg: Message) -> None:
    # TODO сделать
    """
    показывает фото данного отеля
    :param msg: message
    :return: none
    """
    chat_id = msg.chat.id
    # запрос изображений занимает время
    wait_msg = bot.send_message(chat_id, answer('wait', msg))
    params = extract_search_parameters(msg)
    images = ...
    logger.info(f'{get_hotels.__name__} returned: {images}')
    #
    bot.delete_message(chat_id, wait_msg.id)
    if not images or len(images) < 1:
        bot.send_message(chat_id, answer('hotels_not_found', msg))
    elif 'bad_request' in images:
        bot.send_message(chat_id, answer('bad_request', msg))
    else:
        quantity = len(images)
        bot.send_message(chat_id, get_parameters_information(msg))
        bot.send_message(chat_id, f"{answer('images_found', msg)}: {quantity}")
        for hotel in images:
            bot.send_message(chat_id, hotel)


def hotels_list(msg: Message) -> None:
    """
    displays hotel search results in chat
    :param msg: message
    :return: none
    """
    chat_id = msg.chat.id
    wait_msg = bot.send_message(chat_id, answer('wait', msg))

    params = extract_search_parameters(msg)

    hotels = get_hotels(msg, params)
    logger.info(f'function {get_hotels.__name__} returned: {hotels}')
    bot.delete_message(chat_id, wait_msg.id)
    if not hotels or len(hotels) < 1:
        bot.send_message(chat_id, answer('hotels_not_found', msg))
    elif 'bad_request' in hotels:
        bot.send_message(chat_id, answer('bad_request', msg))
    else:
        quantity = len(hotels)
        bot.send_message(chat_id, get_parameters_information(msg))
        bot.send_message(chat_id, f"{answer('hotels_found', msg)}: {quantity}")
        for hotel in hotels:
            bot.send_message(chat_id, hotel)


def get_search_parameters(msg: Message) -> None:
    """
    fixes search parameters
    :param msg: message
    :return: none
    """
    logger.info(f'{get_search_parameters.__name__} called with argument: {msg}')
    chat_id = msg.chat.id
    state = redis_db.hget(chat_id, 'state')
    # проверка корректности
    if not is_input_correct(msg):
        bot.send_message(chat_id, make_message(msg, 'mistake_'))
    else:
        redis_db.hincrby(msg.chat.id, 'state', 1)
        if state == '2':
            min_price, max_price = sorted(msg.text.strip().split(), key=int)
            redis_db.hset(chat_id, steps[state + 'min'], min_price)
            logger.info(f"{steps[state + 'min']} set to {min_price}")
            redis_db.hset(chat_id, steps[state + 'max'], max_price)
            logger.info(f"{steps[state + 'max']} set to {max_price}")
            bot.send_message(chat_id, make_message(msg, 'question_'))
        elif state == '4':
            redis_db.hset(chat_id, steps[state], msg.text.strip())
            logger.info(f"{steps[state]} set to {msg.text.strip()}")
            redis_db.hset(chat_id, 'state', 0)
            hotels_list(msg)
        else:
            redis_db.hset(chat_id, steps[state], msg.text.strip())
            logger.info(f"{steps[state]} set to {msg.text.strip()}")
            bot.send_message(chat_id, make_message(msg, 'question_'))


@bot.callback_query_handler(func=lambda call: True)
def keyboard_handler(call: CallbackQuery) -> None:
    """
    buttons handlers
    :param call: callbackquery
    :return: none
    """
    logger.info(f'{keyboard_handler.__name__} called with argument: {call}')
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)

    if call.data.startswith('code'):
        if redis_db.hget(chat_id, 'state') != '1':
            bot.send_message(call.message.chat.id, answer('enter_command', call.message))
            redis_db.hset(chat_id, 'state', 0)
        else:
            loc_name = exact_location(call.message.json, call.data)
            redis_db.hset(chat_id, mapping={"destination_id": call.data[4:], "destination_name": loc_name})
            logger.info(f"{loc_name} selected")
            bot.send_message(
                chat_id,
                f"{answer('loc_selected', call.message)}: {loc_name}",
            )
            if redis_db.hget(chat_id, 'order') == 'distance_from_landmark':
                redis_db.hincrby(chat_id, 'state', 1)
            else:
                redis_db.hincrby(chat_id, 'state', 3)
            bot.send_message(chat_id, make_message(call.message, 'question_'))


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    обработка текствовых сообщений
    :param message: message
    :return: none
    """

    if not is_user_in_db(message):
        add_user(message)
    state = redis_db.hget(message.chat.id, 'state')
    print(state)
    if state == '1':
        # Первый запрос - назв города
        get_locations(message)
        print('c')
    elif state in ['2', '3', '4']:
        get_search_parameters(message)
    else:
        bot.send_message(message.chat.id, answer('misunderstanding', message))


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f'Unexpected error: {e}')
