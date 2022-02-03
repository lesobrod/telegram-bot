import os
import re
from dotenv import load_dotenv
import requests
from telebot.types import Message
from loguru import logger
from config import IMAGES_URL, API_HOST_URL, IMAGE_SIZE, FULL_LOGS

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

RAPID_API_KEY = os.getenv('RAPID_API_KEY')


def replace_tags(img_url):
    return re.sub(r'\{size\}', IMAGE_SIZE, img_url)


def request_images(hotel_id: str):
    """
    Запрос изображений отеля
    :param hotel_id: String
    :return: data
    """
    querystring = {"id": hotel_id}

    headers = {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': API_HOST_URL
    }
    logger.info(f'Parameters for search images: {querystring}')
    try:
        response = requests.request("GET", IMAGES_URL,
                                    headers=headers, params=querystring, timeout=20)
        data = response.json()
        if FULL_LOGS:
            logger.info(f'Hotels api(images) response received: {data}')
        else:
            len_hotel_img = len(data["hotelImages"])
            len_room_img = len(data["roomImages"])
            logger.info(f'Hotels api(images) response received {len_hotel_img} '
                        f'hotel images and {len_room_img} rooms images')

        if data.get('message'):
            logger.error(f'Problems with subscription to hotels api')
            raise requests.exceptions.RequestException
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f'Server error: {e}')
    except Exception as e:
        logger.error(f'Error: {e}')


def get_images(parameters: dict) -> list:
    """
    Возвращает список URL: сначала фото отеля, потом фото комнат
    :parameters: dict
    :return: list of URL
    """
    data = request_images(parameters['hotel_id'])
    num_hotel_img = int(parameters['num_hotel_img'])
    num_room_img = int(parameters['num_room_img'])
    result = [replace_tags(item.get("baseUrl")) for item in data.get("hotelImages")[:num_hotel_img]]
    result_rooms = [replace_tags(item.get("baseUrl")) for item in
                    [item["images"][0] for item in data.get("roomImages")[:num_room_img]]]
    result.extend(result_rooms)
    return result
