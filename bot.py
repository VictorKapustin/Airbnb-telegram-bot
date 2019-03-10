import json
import logging
import datetime
import re
import requests
from glob import glob

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import airbnb

from settings import PROXY, key_bot

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler('bot.log', 'a', 'utf-8')]
                    )


def menu_keyboard():
    keyboard = ReplyKeyboardMarkup([['Menu', 'Help']], resize_keyboard=True)
    return keyboard


def greet_user(bot, update, user_data):
    text = ("Hi! I'm bot low cost offers finder at Airbnb.\n\n"
            "I will follow your filters and tell you when i find new offer for you.\n\n"
            "It's simple to use me:\n"
            " · Press Menu, to add your first notification or to edit existing\n"
            " · To read full description of bot functions press Help button")

    logging.info(f'@{update.message.chat["username"]} started use the bot')
    update.message.reply_text(text, reply_markup=menu_keyboard())


def menu(bot, update, user_data):
    text = "Do you want to add new search or edit existing?"
    logging.info(f'@{update.message.chat["username"]} called menu')
    keyboard = ReplyKeyboardMarkup([['New search', 'Edit existing search']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, )


def new_search(bot, update, user_data):
    text = "Ok, now please choose your currency"
    keyboard = ReplyKeyboardMarkup([['USD$', 'EUR€', 'RUB₽', 'GBP£']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True)
    return 'curr'


def search_get_curr(bot, update, user_data):
    curr = update.message.text[:3]
    user_data['currency'] = curr
    text = 'ok, now write city name where you want to go'
    update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return 'city'


def set_city(bot, update, user_data):
    city = update.message.text
    user_data['city'] = city
    text = 'When do you want to check in? Date format: YYYY-MM-DD'
    update.message.reply_text(text)
    return 'checkin'

def checkin(bot, update, user_data):
    check_in = update.message.text
    user_data['check_in'] = check_in
    text = 'What is the last day of your stay? Date format: YYYY-MM-DD'
    update.message.reply_text(text)
    return 'checkout'


def checkout(bot, update, user_data):
    check_out = update.message.text
    user_data['check_out'] = check_out
    text = 'How many guests?'
    keyboard = ReplyKeyboardMarkup([['1', '2', '3'], ['4', '5', '6']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True, resize_keyboard=True)
    return 'adult'


def adult(bot, update, user_data):
    adults = update.message.text
    user_data['adult'] = adults
    text = 'Choose room type'
    keyboard = ReplyKeyboardMarkup([['Entire home/apt', 'Private room', 'Shared room']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True, resize_keyboard=True)
    return 'room'


def add_room(bot, update, user_data):
    room = update.message.text
    user_data['room_type'] = [room]
    text = "What is your maximum price per night? Only digits"
    update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return 'maxprice'


def max_price(bot, update, user_data):
    maxprice = update.message.text
    user_data['max_price'] = maxprice
    text = 'Thank you, now check your filters\n'
    text += f'Your currency: {user_data["currency"]}\nCity: {user_data["city"]}\nCheck in date: {user_data["check_in"]}\n'
    text += f'Check out date: {user_data["check_out"]}\nNumber of guests: {user_data["adult"]}\n'
    text += f'Room type: {user_data["room_type"]}\nMaximum price: {user_data["max_price"]}'
    update.message.reply_text(text)
    search_home(bot, update, user_data)
    return


def search_home(bot, update, user_data):

    api = airbnb.Api(randomize=True, currency=user_data["currency"])
    print(user_data)
    homes = api.get_homes(query=user_data['city'], adults=user_data["adult"], price_max=user_data["max_price"],
                          checkin=user_data["check_in"], checkout=user_data["check_out"], room_types=user_data["room_type"])

    with open('api_response.json', 'w') as file:
        json.dump(homes, file)


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

    dp.add_handler(RegexHandler('^(Menu)$', menu, pass_user_data=True))
    dp.add_handler(search)

    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
