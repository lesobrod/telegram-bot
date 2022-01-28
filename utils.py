# import re
from datetime import datetime, timedelta

from telebot.types import Message
from loguru import logger

from my_redis import redis_db
from config import MESSAGE_DICT, FULL_LOGS

steps = {
    '1': 'destination_id',
    '2min': 'min_price',
    '2max': 'max_price',
    '3': 'distance',
    '4': 'quantity',
    '5': 'images'
}


def answer(key: str) -> str:
    """
    Возвращает подходящий ответ из MESSAGE_DICT
    :param key: str key
    :return: text
    """
    return MESSAGE_DICT[key]


def make_message(msg: Message, prefix: str) -> str:
    """
    Формирование сложного сообщения
    :param msg: Message
    :param prefix: string
    :return: string
    """
    state = redis_db.hget(msg.chat.id, 'state')
    message = answer(prefix + state)

    return message


def str_to_limit(num: str, limit: str) -> str:
    """
    Приводит число к максимальному значению Принимает и возвращает строки
    :param num: int as str
    :param limit: int as str
    :return: string
    """
    if int(num) > int(limit):
        return limit
    else:
        return num


def is_input_correct(msg: Message) -> bool:
    """
    Проверка корректности ввода
    :param msg: Message
    :return: True/None
    """
    state = redis_db.hget(msg.chat.id, 'state')
    msg = msg.text.strip()
    if state == '5' and msg.replace(' ', '').isdigit():
        return True
    if state == '4' and ' ' not in msg and msg.isdigit():
        return True
    elif state == '3' and ' ' not in msg and msg.replace('.', '').isdigit():
        return True
    elif state == '2' and msg.replace(' ', '').isdigit() and len(msg.split()) == 2:
        return True
    elif state == '1' and msg.replace(' ', '').replace('-', '').isalpha():
        return True


def get_parameters_information(msg: Message) -> str:
    """
    Возвращает сложное сообщение с информацией о параметрах поиска
    :param msg: Message
    :return: Text
    """
    if FULL_LOGS:
        logger.info(f'get_parameters_information called with argument: {msg}')
    else:
        logger.info(f'get_parameters_information called with argument: {msg.json}')
    parameters = redis_db.hgetall(msg.chat.id)
    sort_order = parameters['order']
    city = parameters['destination_name']
    message = (
        f"<b>{answer('parameters')}</b>\n"
        f"{answer('city')}: {city}\n"
    )
    if sort_order == "DISTANCE_FROM_LANDMARK":
        price_min = parameters['min_price']
        price_max = parameters['max_price']
        distance = parameters['distance']
        message += f"{answer('price')}: {price_min} - {price_max} \n" \
                   f"{answer('max_distance')}: {distance}"
    logger.info(f'Search parameters: {message}')
    return message


def hotel_price(hotel: dict) -> int:
    """
    Стоимость проживания
    :param hotel: dict - hotel information
    :return: integer or float like number
    """
    price = 0
    try:
        price = hotel.get('ratePlan').get('price').get('exactCurrent')
    except Exception as e:
        logger.warning(f'Hotel price getting error {e}')
    return price


def hotel_address(hotel: dict) -> str:
    """
    Возвращает адрес отеля
    :param hotel: dict
    :return: hotel address
    """
    message = answer('no_information')
    if hotel.get('address'):
        message = hotel.get('address').get('streetAddress', message)
    return message


def hotel_distance(hotel: dict) -> str:
    """
    Возвращает расстояние до центра в км
    :param msg: Message
    :param hotel: dict
    :return: hotel distance
    """
    message = answer('no_information')
    data = hotel.get('landmarks')[0].get('distance')
    if data:
        # Переводим в км
        result = float(data.replace('miles', '')) * 1.61
        message = f'{result:.1f} км'
    return message


def hotel_rating(rating: float, msg: Message) -> str:
    """
    Возвращает рейтинг отеля значками
    :param rating: hotel rating
    :param msg: Message
    :return: string
    """
    if not rating:
        return answer('no_information')
    return '⭐' * int(rating)


def check_in_n_out_dates(check_in: datetime = None, check_out: datetime = None) -> dict:
    """
    Приведение дат в нужный формат
    Если дат нет - установка на сегодня-завтра
    :param check_in: check-in date
    :param check_out: check-out date
    :return: dict with check-in and check-out dates
    """
    dates = {}
    if not check_in:
        check_in = datetime.now()
    if not check_out:
        check_out = check_in + timedelta(1)

    dates['check_in'] = check_in.strftime("%Y-%m-%d")
    dates['check_out'] = check_out.strftime("%Y-%m-%d")

    return dates


def add_user(msg: Message) -> None:
    """
    Добавляем пользователя в базу
    :param msg: Message
    :return: None
    """
    logger.info("add_user called")
    chat_id = msg.chat.id
    # Initial state 0
    redis_db.hset(chat_id, mapping={
        "state": 0,
    })


def is_user_in_db(msg: Message) -> bool:
    """
    Проверка, есть ли пользователь в базе
    :param msg: Message
    :return: True если да
    """
    logger.info('is_user_in_db called')
    chat_id = msg.chat.id
    return redis_db.hget(chat_id, 'state')


def extract_search_parameters(msg: Message) -> dict:
    """
    Извлекаем данные из базы
    :param msg: Message
    :return: dict
    """
    logger.info(f"extract_search_parameters called")
    params = redis_db.hgetall(msg.chat.id)
    logger.info(f"parameters: {params}")
    return params
