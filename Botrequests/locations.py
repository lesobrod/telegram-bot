import os
import re
from dotenv import load_dotenv
import requests
from telebot.types import Message
from loguru import logger
from my_redis import redis_db
from config import LOCATIONS_URL, API_HOST_URL, \
    FULL_LOGS, CURRENCY, LOCALE

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

RAPID_API_KEY = os.getenv('RAPID_API_KEY')


def exact_location(data: dict, loc_id: str) -> str:
    """
    Возвращает название локации по id
    :param data: dict Message
    :param loc_id: location id
    :return: location name
    """
    for loc in data['reply_markup']['inline_keyboard']:
        if loc[0]['callback_data'] == loc_id:
            return loc[0]['text']


def delete_tags(html_text):
    text = re.sub(r'<([^<>]*)>', '', html_text)
    return text


def request_locations(msg: Message):
    """
    Запрос возможных геолокаций
    :param msg: Message
    :return: data
    """

    querystring = {
        "query": msg.text.strip(),
        "locale": LOCALE,
        "currency": CURRENCY
    }

    headers = {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': API_HOST_URL
    }
    logger.info(f'Parameters for search locations: {querystring}')

    try:
        response = requests.request("GET", LOCATIONS_URL,
                                    headers=headers, params=querystring, timeout=20)
        data = response.json()
        if FULL_LOGS:
            logger.info(f'Hotels api(locations) response received: {data}')

        if data.get('message'):
            logger.error(f'Problems with subscription to hotels api {data}')
            raise requests.exceptions.RequestException

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f'Server error: {e}')
    except Exception as e:
        logger.error(f'Error: {e}')


def make_locations_list(msg: Message) -> dict:
    """
    Создание словаря локаций
    :param msg: Message
    :return: dict: location name - location id
    """
    data = request_locations(msg)
    if not data:
        return {'bad_request': 'bad_request'}

    try:
        locations = dict()
        work_data = data.get('suggestions')[0].get('entities')
        if len(work_data) > 0:
            for item in work_data:
                location_name = delete_tags(item['caption'])
                locations[location_name] = item['destinationId']
            logger.info(f'Locations dict: {locations}')
            return locations
    except Exception as e:
        logger.error(f'Could not parse hotel api response. {e}')
