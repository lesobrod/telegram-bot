import os
from dotenv import load_dotenv
import requests
from loguru import logger
from telebot.types import Message
from config import PROPERTIES_URL, API_HOST_URL, HOTELS_URL,\
    FULL_LOGS, CURRENCY, MAX_QUANTITY
from utils import check_in_n_out_dates, hotel_price, \
    answer, hotel_address, hotel_rating, hotel_distance
# from my_redis import redis_db

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.template')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

RAPID_API_KEY = os.getenv('RAPID_API_KEY')


def get_hotels(msg: Message, parameters: dict) -> [list, None]:
    """
    Обработка данных об отелях
    :param msg: Message
    :param parameters: search parameters
    :return: list
    """
    data = request_hotels(parameters)
    if 'bad_req' in data:
        return ['bad_request']
    data = handle_hotels_info(msg, data)
    if not data or len(data['results']) < 1:
        return None
    if parameters['order'] == 'DISTANCE_FROM_LANDMARK':
        distance = float(parameters['distance'])
        quantity = int(parameters['quantity'])
        data = choose_best_hotels(data['results'], distance, quantity)
    else:
        data = data['results']

    data = generate_hotels_descriptions(data, msg)
    return data


def request_hotels(parameters: dict):
    """
    Запрос информации из hotel api
    :param parameters
    :return: response from hotel api
    """
    logger.info(f'request_hotels called with  parameters = {parameters}')
    dates = check_in_n_out_dates()

    querystring = {
        "adults1": "1",
        "pageNumber": "1",
        "destinationId": parameters['destination_id'],
        "pageSize": parameters['quantity'],
        "checkOut": dates['check_out'],
        "checkIn": dates['check_in'],
        "sortOrder": parameters['order'],
        "currency": CURRENCY
    }
    if parameters['order'] == 'DISTANCE_FROM_LANDMARK':
        querystring['priceMax'] = parameters['max_price']
        querystring['priceMin'] = parameters['min_price']
        querystring['pageSize'] = MAX_QUANTITY

    logger.info(f'Search parameters: {querystring}')

    headers = {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': API_HOST_URL
    }

    try:
        response = requests.request("GET", PROPERTIES_URL,
                                    headers=headers, params=querystring, timeout=20)
        data = response.json()
        if data.get('message'):
            raise requests.exceptions.RequestException
        if FULL_LOGS:
            logger.info(f'Hotels api(properties/list) response received: {data}')
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f'Error receiving response: {e}')
        return {'bad_req': 'bad_req'}
    except Exception as e:
        logger.info(f'Error in function request_hotels: {e}')
        return {'bad_req': 'bad_req'}


def handle_hotels_info(msg: Message, data: dict) -> dict:
    """
    Глубокая обработка информации по отелю
    :param msg: Message
    :param data: hotel data
    :return: dict of handled hotel data
    """
    if FULL_LOGS:
        logger.info(f'handle_hotels_info called with argument: msg = {msg}, data = {data}')
    data = data.get('data', {}).get('body', {}).get('searchResults')
    hotels = dict()
    hotels['total_count'] = data.get('totalCount', 0)
    hotels['results'] = []

    try:
        if hotels['total_count'] > 0:
            for cur_hotel in data.get('results'):
                hotel = dict()
                hotel['hotel_id'] = cur_hotel.get('id')
                hotel['name'] = cur_hotel.get('name')
                hotel['star_rating'] = cur_hotel.get('starRating', 0)
                hotel['price'] = hotel_price(cur_hotel)
                hotel['distance'] = hotel_distance(cur_hotel)
                hotel['address'] = hotel_address(cur_hotel)

                if hotel not in hotels['results']:
                    hotels['results'].append(hotel)
        logger.info(f'Hotels in function handle_hotels_info: {hotels}')
        return hotels

    except Exception as e:
        logger.info(f'Error in function handle_hotels_info: {e}')


def choose_best_hotels(hotels: list[dict], distance: float, limit: int) -> list[dict]:
    """
    Отбор и сортировка отелей по параметрам
    :param limit: quantity limit
    :param distance: distance limit
    :param hotels: dict
    :return: choosen hotels
    """

    def dist_filter(elem: dict) -> bool:
        return float(elem["distance"].strip().replace(',', '.').split()[0]) <= distance

    logger.info(f'choose_best_hotels called with arguments: '
                f'distance = {distance}, quantity = {limit}\n{hotels}')
    hotels = list(filter(dist_filter, hotels))
    logger.info(f'Hotels filtered: {hotels}')
    hotels = sorted(hotels, key=lambda k: k["price"])
    logger.info(f'Hotels sorted: {hotels}')
    if len(hotels) > limit:
        hotels = hotels[:limit]
    return hotels


def generate_hotels_descriptions(hotels: dict, msg: Message):
    """
    Создание конечной карточки отеля
    :param msg:
    :param hotels:
    :return:
    """
    logger.info(f'generate_hotels_descriptions called with argument {hotels}')
    hotels_info = []

    for hotel in hotels:
        # Возвращает текстовое сообщение и ID
        message = (hotel.get('hotel_id'),

                   f"Отель:  <a href='{HOTELS_URL}{hotel.get('hotel_id')}/'>{hotel.get('name')}</a>\n"
                   f"Рейтинг: {hotel_rating(hotel.get('star_rating'), msg)}\n"
                   f"Цена: {hotel['price']} {CURRENCY}\n"
                   f"Расстояние до центра: {hotel.get('distance')}\n"
                   f"Адрес: {hotel.get('address')}\n"
                   )
        hotels_info.append(message)

    return hotels_info
