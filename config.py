# BOT_NAME = 'HeartTravelBot'
# DATA_BASE_NAME = 'HeartTravel'

DATA_BASE_ENDPOINT = 'redis-17913.c281.us-east-1-2.ec2.cloud.redislabs.com'

API_HOST_URL = "hotels4.p.rapidapi.com"
LOCATIONS_URL = "https://hotels4.p.rapidapi.com/locations/search"
PROPERTIES_URL = "https://hotels4.p.rapidapi.com/properties/list"
IMAGES_URL = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
HOTELS_URL = "https://ru.hotels.com/ho"

MAX_IMG_QUANTITY = "10"
MAX_USER_QUANTITY = "20"
MAX_API_QUANTITY = "100"

LOCALE = "ru_RU"
# Валюта
CURRENCY = "USD"
# Код размера изображений
IMAGE_SIZE = "y"
# Лог файл
SINK = "logs/bot.log"
# Стираем ли лог файлы в начале
CLEAR_LOGS = True
# Пишем ли длинные логи
FULL_LOGS = False
# Дублировать ли лог в терминал
MONITOR_LOGS = True

LOGGER_CONFIG = {
    "handlers": [
        {
            "sink": SINK,
            "format": "{level} | {time:YYYY-MMM-D HH:mm:ss} | {message}",
            "encoding": "utf-8",
            "level": "DEBUG",
            "rotation": "5 MB",
            "compression": "zip"
        },
    ],
}

MESSAGE_DICT = {
    'help':
        '<b>Команды бота</b>\n'
        '/help - список всех команд\n'
        '/lowprice - отели с низкими ценами\n'
        '/highprice - отели с высокими ценами\n'
        '/bestdeal - лучшие предложения\n'
        '/history - история поиска\n',
    'hello':
        'Рад приветствовать вас! \nНачните с команды /help.',
    'mistake_1':
        'Некорректный ввод. Название города должно содержать только буквы латиницы/кириллицы и '
        'символ "-". Попробуйте еще раз.',
    'mistake_2':
        'Некорректный ввод. Нужно ввести два целых числа, разделенных пробелом. Повторите еще раз.',
    'mistake_3':
        'Некорректный ввод. Нужно ввести число, возможно с демятичной дробью. Повторите еще раз.',
    'mistake_4':
        'Некорректный ввод. Ввелите целое число '
        'раз.',
    'mistake_5':
        'Некорректный ввод. Нужно ввести два целых числа, разделенных пробелом. Пример "3 '
        '5", или нули, если не нужны фото. Повторите еще раз.',
    'question_1':
        'В каком городе искать отели?',
    'question_2':
        f'Введите диапазон цен (в {CURRENCY}) через пробел:',
    'question_3':
        'Введите радиус поиска от центра города в км',
    'question_4':
        'Cколько отелей вывести (макс 20):',
    'question_5':
        'Сколько фото отеля вывести\n(макс 10, 0 - не выводятся), \n'
        'и сколько фото комнат \n(макс 10, 0 - не выводятся) \nчерез пробел: ',
    'locations_not_found':
        'Локация не найдена, попробуйте другие варианты',
    'hotels_not_found':
        'Отели не найдены. Попробуйте ввести иные параметры.',
    'images_not_found':
        'Нет фото',
    'bad_request':
        'К сожалению, сервер недоступен, повторите поиск позже.',
    'distance':
        'Расстояние до центра города',
    'loc_choose':
        'Выберите город из списка:',
    'loc_selected':
        'Выбрана локация',
    'cancel':
        'Отмена',
    'ask_to_select':
        'Выберите один из вариантов:',
    'canceled':
        'Отменено',
    'hotels_found':
        'Найдено отелей',
    'images_found':
        'Найдено изображений',
    'misunderstanding':
        'Некорректная команда. Вызовите /help.',
    'wait':
        'Пожалуйста, подождите\nОжидаю данные...',
    'parameters':
        'Параметры поиска',
    'rating':
        'Класс отеля',
    'city':
        'Город',
    'price':
        'Стоимость'
    ,
    'max_distance':
        'Максимальное расстояние до центра города',

    'no_information':
        'Нет данных',
    'no_history':
        'В истории пока ничего нет',
    'enter_command':
        'Пожалуйста, сначала введите нужную команду'
}
