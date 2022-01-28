import os
from dotenv import load_dotenv
from my_redis import redis_db
import config
import telebot
from loguru import logger
from telebot.types import Message, CallbackQuery
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from botrequests.hotels import get_hotels
from botrequests.locations import exact_location, make_locations_list
from botrequests.images import get_images
from utils import is_input_correct, get_parameters_information, \
    make_message, steps, answer, str_to_limit, \
    is_user_in_db, add_user, extract_search_parameters

logger.configure(**config.LOGGER_CONFIG)
# Базовые команды и результаты поиса по ним логгируются с тегами "HIST" и "HIST-COM"
logger.level(name="HIST", no=25, color="<blue>", icon="@")
logger.level(name="HIST-COM", no=25, color="<blue>", icon="@")

# Если установлено, выводим лог в терминал
if config.MONITOR_LOGS:
    logger.add(sink=lambda msg: print(msg, end=''),
               format="{level} | {time:YYYY-MMM-D HH:mm:ss} | {message}")

# Если установлкено, очищаем лог-файл
if config.CLEAR_LOGS:
    with open(config.SINK, 'w') as file:
        file.truncate()

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Стационарная клава
keyboard = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
row = [KeyboardButton(text="/lowprice"), KeyboardButton(text="/highprice"),
       KeyboardButton(text="/bestdeal")]
keyboard.add(*row)
row = [KeyboardButton(text="/help"), KeyboardButton(text="/history")]
keyboard.add(*row)


@bot.message_handler(commands=['help', 'start'])
def get_command_help(message: Message) -> None:
    """
    Обработка команд /help, /start
    :param message: message
    :return: none
    """
    chat_id = message.chat.id
    if not is_user_in_db(message):
        add_user(message)

    if 'start' in message.text:
        logger.info(f'"start" command is called by {chat_id}')
        bot.send_message(chat_id, answer('hello'), reply_markup=keyboard)
    else:
        logger.info(f'"help" command is called by {chat_id}')
        bot.send_message(chat_id, answer('help'))


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def get_searching_commands(message: Message) -> None:
    """
    Обработка основных команд
    :param message: Message
    :return: None
    """
    keyboard = ReplyKeyboardRemove()
    if not is_user_in_db(message):
        add_user(message)

    chat_id = message.chat.id
    # Если команда поступила state = 1
    redis_db.hset(chat_id, 'state', 1)

    if 'lowprice' in message.text:
        redis_db.hset(chat_id, 'order', 'PRICE')
        logger.log("HIST-COM", f'Команда /lowprice | {chat_id}')

    elif 'highprice' in message.text:
        redis_db.hset(chat_id, 'order', 'PRICE_HIGHEST_FIRST')
        logger.log("HIST-COM", f'Команда /highprice | {chat_id}')

    else:
        redis_db.hset(chat_id, 'order', 'DISTANCE_FROM_LANDMARK')
        logger.log("HIST-COM", f'Команда /bestdeal | {chat_id}')

    logger.info(redis_db.hget(chat_id, 'order'))
    state = redis_db.hget(chat_id, 'state')
    logger.info(f"Current state: {state}")
    bot.send_message(chat_id, make_message(message, 'question_'))


@bot.message_handler(commands=['history'])
def get_command_history(message: Message) -> None:
    """
    Обработка команды /history
    :param message: message
    :return: none
    """
    if not is_user_in_db(message):
        add_user(message)

    chat_id = message.chat.id
    logger.info(f'"history" command is called by {chat_id}')
    history = ''
    with open(config.SINK, 'r', encoding='UTF-8') as file:
        for line in file:
            if line.startswith("HIST"):
                data = line.split('|')
                if data[3].strip() == str(chat_id):
                    if data[0].strip() == "HIST-COM":
                        history += f'{data[1]}\n{data[2]}\n'
                    else:
                        history += f'{data[2]}\n'

        if history == '':
            bot.send_message(chat_id, answer('no_history'))
        else:
            bot.send_message(chat_id, history,
                             disable_web_page_preview=True)


def get_locations(msg: Message) -> None:
    """
    Выбор возможных геолокаций по названию
    :param msg: message
    :return: none
    """
    if not is_input_correct(msg):
        bot.send_message(msg.chat.id, make_message(msg, 'mistake_'))
    else:
        # Предупрежд об ожидании
        wait_msg = bot.send_message(msg.chat.id, answer('wait'))

        # Данные о возможных локациях
        locations = make_locations_list(msg)

        bot.delete_message(msg.chat.id, wait_msg.id)

        if not locations or len(locations) < 1:
            bot.send_message(msg.chat.id, answer('locations_not_found'))
        elif locations.get('bad_request'):
            bot.send_message(msg.chat.id, answer('bad_request'))
        else:
            menu = InlineKeyboardMarkup()

            for loc_name, loc_id in locations.items():
                menu.add(InlineKeyboardButton(text=loc_name,
                                              callback_data='code' + loc_id))

            menu.add(InlineKeyboardButton(text='Сancel', callback_data='cancel'))

            bot.send_message(msg.chat.id, 'Выбор города', reply_markup=menu)


def images_list(msg: Message) -> None:
    """
    Отображает фото отеля
    :param: msg
    :return: none
    """
    chat_id = msg.chat.id
    params = extract_search_parameters(msg)
    images = get_images(msg, params)

    logger.info(f'get_images returned: {images}')

    if images == 'not_found':
        bot.send_message(chat_id, answer('images_not_found'))
    else:
        for img in images:
            bot.send_photo(chat_id=chat_id, photo=img)


def hotels_list(msg: Message) -> None:
    """
    Отображает список отелей
    :param msg: message
    :return: none
    """
    chat_id = msg.chat.id
    wait_msg = bot.send_message(chat_id, answer('wait'))

    params = extract_search_parameters(msg)

    hotels = get_hotels(msg, params)

    logger.info(f'get_hotels returned: {hotels}')
    bot.delete_message(chat_id, wait_msg.id)
    if not hotels or len(hotels) < 1:
        bot.send_message(chat_id, answer('hotels_not_found'))
    elif 'bad_request' in hotels:
        bot.send_message(chat_id, answer('bad_request'))
    else:
        quantity = len(hotels)
        bot.send_message(chat_id, get_parameters_information(msg))
        bot.send_message(chat_id, "{}: {}".format(answer('hotels_found'), quantity))
        for hotel in hotels:
            # hotel[0] - ID, hotel[1] - message
            redis_db.hset(chat_id, 'hotel_id', hotel[0])
            #  parse_mode='HTML' ВАЖНО , но уже указано при создании бота
            bot.send_message(chat_id, hotel[1], disable_web_page_preview=True)
            if redis_db.hget(chat_id, 'show_images') == '1':
                images_list(msg)
            # Формат из-за \n
            logger.log("HIST",
                       '{} | {}'.format(hotel[1].split("\n")[0], chat_id))


def get_search_parameters(msg: Message) -> None:
    """
    Разбор параметров текстового сообщения
    :param msg: message
    :return: none
    """
    if config.FULL_LOGS:
        logger.info(f'get_search_parameters called with argument: {msg}')
    else:
        logger.info(f'get_search_parameters called with argument: {msg.json}')
    chat_id = msg.chat.id
    state = redis_db.hget(chat_id, 'state')
    msg_data = msg.text.strip()

    # проверка корректности
    if not is_input_correct(msg):
        bot.send_message(chat_id, make_message(msg, 'mistake_'))
    else:
        redis_db.hincrby(msg.chat.id, 'state', 1)
        logger.info(f"Current state in  get_search_parameters: {state}")
        if state == '2':
            min_price, max_price = sorted(msg_data.split(), key=int)
            redis_db.hset(chat_id, steps[state + 'min'], min_price)
            logger.info(f"{steps[state + 'min']} set to {min_price}")
            redis_db.hset(chat_id, steps[state + 'max'], max_price)
            logger.info(f"{steps[state + 'max']} set to {max_price}")

            bot.send_message(chat_id, make_message(msg, 'question_'))

        elif state == '4':
            # Выводим не более MAX_USER_QUANTITY отелей
            set_data = str_to_limit(msg_data, config.MAX_USER_QUANTITY)
            redis_db.hset(chat_id, steps[state], set_data)
            logger.info(f"{steps[state]} set to {set_data}")

            menu = InlineKeyboardMarkup()
            menu.add(InlineKeyboardButton(text='Да', callback_data='img yes'))
            menu.add(InlineKeyboardButton(text='Нет', callback_data='img no'))
            bot.send_message(chat_id, 'Вывести фото?', reply_markup=menu)

        elif state == '5':
            set_data = msg_data.split()
            # Если указано одно число, выводим столько фото отеля,
            # но не более MAX_IMG_QUANTITY
            num_hotel_img = str_to_limit(set_data[0], config.MAX_IMG_QUANTITY)
            redis_db.hset(chat_id, 'num_hotel_img', num_hotel_img)
            logger.info(f"num_hotel_img set to {num_hotel_img}")
            if len(set_data) == 1:
                redis_db.hset(chat_id, 'num_room_img', '0')
                logger.info(f"num_room_img set to 0")
            else:
                # Если указано два - используем их оба
                num_room_img = str_to_limit(set_data[1], config.MAX_IMG_QUANTITY)
                redis_db.hset(chat_id, 'num_room_img', num_room_img)
                logger.info(f"num_room_img set to {num_room_img}")

            redis_db.hset(chat_id, 'state', 0)

            hotels_list(msg)

        else:
            redis_db.hset(chat_id, steps[state], msg_data)
            logger.info(f"{steps[state]} set to {msg_data}")
            bot.send_message(chat_id, make_message(msg, 'question_'))


@bot.callback_query_handler(func=lambda call: True)
def keyboard_handler(call: CallbackQuery) -> None:
    """
    Обработка кнопок
    :param call: callbackquery
    :return: none
    """
    chat_id = call.message.chat.id
    if config.FULL_LOGS:
        logger.info(f'keyboard_handler called with argument: {call}')
    else:
        logger.info(f'keyboard_handler called with argument: {call.message.json}')

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)

    if call.data.startswith('code'):
        # Обработка выбора локации
        print('state=', redis_db.hget(chat_id, 'state'))
        if redis_db.hget(chat_id, 'state') != '1':
            # Если сначала, то напоминаем ввести команду
            bot.send_message(call.message.chat.id, answer('enter_command'))
            redis_db.hset(chat_id, 'state', 0)
        else:
            loc_name = exact_location(call.message.json, call.data)
            # Заводим в базу название локации
            redis_db.hset(chat_id, mapping={"destination_id": call.data[4:],
                                            "destination_name": loc_name})
            logger.info(f"Location {loc_name} selected")
            bot.send_message(
                chat_id,
                "{}: {}".format(answer('loc_selected'), loc_name),
            )
            if redis_db.hget(chat_id, 'order') == 'DISTANCE_FROM_LANDMARK':
                redis_db.hincrby(chat_id, 'state', 1)
            else:
                redis_db.hincrby(chat_id, 'state', 3)
            bot.send_message(chat_id, make_message(call.message, 'question_'))

    elif call.data.startswith('img'):
        # Обработка да/нет фото
        if call.data.endswith('no'):
            logger.info("'show_images' set to 0")
            redis_db.hset(chat_id, 'show_images', 0)
            hotels_list(call.message)
        else:
            logger.info("'show_images' set to 1")
            redis_db.hset(chat_id, 'show_images', 1)
            redis_db.hset(chat_id, 'state', 5)
            bot.send_message(chat_id, answer('question_5'))


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    Обработка текстовых сообщений
    :param message: message
    :return: none
    """
    if not is_user_in_db(message):
        add_user(message)
    state = redis_db.hget(message.chat.id, 'state')
    logger.info(f"Current state in  get_text_messages: {state}")
    if state == '1':
        # Первый запрос - назв города
        get_locations(message)
    elif state in ['2', '3', '4', '5']:
        get_search_parameters(message)
    else:
        bot.send_message(message.chat.id, answer('misunderstanding'))


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f'Unexpected error: {e}')
