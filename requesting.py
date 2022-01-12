import os
import logging
import requests
from telebot.types import Message
from telebot import logger

from utilites import check_in_n_out_dates, hotel_price, _, hotel_address, \
    hotel_rating
from bot_redis import redis_db

X_RAPIDAPI_KEY = os.getenv('RAPID_API_KEY')
