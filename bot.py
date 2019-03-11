import json
import logging
from datetime import datetime
import re
import requests
from glob import glob

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import airbnb
from functions import *
from settings import PROXY, key_bot

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler('bot.log', 'a', 'utf-8')]
                    )


def main():

    mybot = Updater(key_bot, request_kwargs=PROXY)
    logging.info('Bot is starting')
    state = {
        "curr": [MessageHandler(Filters.text, search_get_curr, pass_user_data=True)],
        "city": [MessageHandler(Filters.text, set_city, pass_user_data=True)],
        "checkin": [MessageHandler(Filters.text, checkin, pass_user_data=True)],
        "checkout": [MessageHandler(Filters.text, checkout, pass_user_data=True)],
        'room': [MessageHandler(Filters.text, add_room, pass_user_data=True)],
        'adult': [MessageHandler(Filters.text, adult, pass_user_data=True)],
        'call_home': [MessageHandler(Filters.text, search_home, pass_user_data=True)],
        'maxprice': [MessageHandler(Filters.text, max_price, pass_user_data=True)]
    }
    entry_point = [RegexHandler('^(New search)$', new_search, pass_user_data=True)]
    search = ConversationHandler(entry_points=entry_point, states=state, fallbacks=[])

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler('start', greet_user, pass_user_data=True))
    dp.add_handler(RegexHandler('^(My subscriptions)$', my_subs, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Menu)$', menu, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Help)$', help_comm, pass_user_data=True))
    dp.add_handler(search)
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
