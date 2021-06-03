from telebot import TeleBot
import os

bot = TeleBot(os.environ.get('TOKEN'))
URL = os.environ.get('URL_WEBHOOK')

if URL.endswith('/'):
    URL += '/'

