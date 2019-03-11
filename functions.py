import json
import logging
from datetime import datetime
import re
import requests
from glob import glob

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import airbnb

from settings import PROXY, key_bot

search_id = 0




def greet_user(bot, update, user_data):
    text = ("Hi! I'm bot low cost offers finder at Airbnb.\n\n"
            "I will follow your filters and tell you when i find new offer for you.\n\n"
            "It's simple to use me:\n"
            " · Press Menu, to add your first notification or to edit existing\n"
            " · To read full description of bot functions press Help button")
    logging.info(f'@{update.message.chat["username"]} called greet_user')
    keyboard = ReplyKeyboardMarkup([['Menu', 'My subscriptions', 'Help']], resize_keyboard=True)
    if update.message.chat["username"] in user_data:
        update.message.reply_text(text, reply_markup=keyboard)
        print(user_data)
    else:
        user_data[update.message.chat["username"]] = {}
        update.message.reply_text(text, reply_markup=keyboard)
        print(user_data)


def menu(bot, update, user_data):
    text = "Do you want to add new search or edit existing?"
    logging.info(f'@{update.message.chat["username"]} called menu')
    keyboard = ReplyKeyboardMarkup([['New search', 'Edit existing search']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, )


def new_search(bot, update, user_data):
    global search_id
    search_id += 1
    user_data[update.message.chat["username"]][search_id] = {}
    user_data[update.message.chat["username"]][search_id]['search_id']= search_id
    logging.info(f'@{update.message.chat["username"]} started new subscription')
    text = "Ok, now please choose your currency"
    keyboard = ReplyKeyboardMarkup([['USD$', 'EUR€', 'RUB₽', 'GBP£']], resize_keyboard=True)
    update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True)
    print(user_data)
    return 'curr'


def search_get_curr(bot, update, user_data):
    curr = update.message.text[:3]
    if curr not in ['USD', 'EUR', 'RUB', 'GBP']:
        text = 'Sorry this currency is not supported, please choose one of these'
        keyboard = ReplyKeyboardMarkup([['USD$', 'EUR€', 'RUB₽', 'GBP£']], resize_keyboard=True)
        update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True)
        return 'curr'
    else:
        user_data[update.message.chat["username"]][search_id]['currency'] = curr
        text = 'ok, now write city name where you want to go'
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        print(user_data)
        return 'city'


def set_city(bot, update, user_data):
    city = update.message.text
    if len(city) < 2:
        text = ('Sorry, you entered wrong city, length of city name should be longer than 2 letters, ' +
                'now write city name where you want to go')
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'
    else:
        user_data[update.message.chat["username"]][search_id]['city'] = city
        text = 'When do you want to check in? Date format: YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkin'


def checkin(bot, update, user_data):
    check_in = update.message.text
    template = r'\d{4}-\d\d-\d\d'
    match = re.fullmatch(template, check_in)

    if match:
        date = datetime.strptime(check_in, '%Y-%m-%d')
        if date > datetime.now():
            user_data[update.message.chat["username"]][search_id]['check_in'] = check_in
            text = 'What is the last day of your stay? Date format: YYYY-MM-DD'
            update.message.reply_text(text)
            return 'checkout'
        else:
            text = 'Your date is in the past, please enter date in future, format: YYYY-MM-DD'
            update.message.reply_text(text)
            return 'checkin'
    else:
        text = 'Your date is incorrect, please enter date in format YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkin'


def checkout(bot, update, user_data):
    check_out = update.message.text
    template = r'\d{4}-\d{2}-\d{2}'
    match = re.fullmatch(template, check_out)
    if match:
        date = datetime.strptime(check_out, '%Y-%m-%d')
        check_in = datetime.strptime(user_data[update.message.chat["username"]][search_id]['check_in'], '%Y-%m-%d')
        if check_in < date:
            user_data[update.message.chat["username"]][search_id]['check_out'] = check_out
            text = 'How many guests?'
            keyboard = ReplyKeyboardMarkup([['1', '2', '3'], ['4', '5', '6']], resize_keyboard=True)
            update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True, resize_keyboard=True)
            return 'adult'
        else:
            text = 'Your date of checkout is earlier than check in, please enter valid date, format: YYYY-MM-DD'
            update.message.reply_text(text)
            return 'checkout'
    else:
        text = 'Your date is incorrect, please enter date in format YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkout'


def adult(bot, update, user_data):
    adults = update.message.text
    match = re.fullmatch(r'\d', adults)
    if match:
        if 6 < int(adults) < 1:
            text = 'Please enter number of guests from 1 to 6'
            update.message.reply_text(text)
            return 'adult'
        else:
            user_data[update.message.chat["username"]][search_id]['adult'] = adults
            text = 'Choose room type'
            keyboard = ReplyKeyboardMarkup([['Entire home/apt', 'Private room', 'Shared room']], resize_keyboard=True)
            update.message.reply_text(text, reply_markup=keyboard, one_time_keyboard=True, resize_keyboard=True)
            return 'room'
    else:
        text = 'Please enter one digit, number of guests'
        update.message.reply_text(text)
        return 'adult'


def add_room(bot, update, user_data):
    room = update.message.text
    user_data[update.message.chat["username"]][search_id]['room_type'] = [room]
    text = "What is your maximum price per night? Only digits"
    update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return 'maxprice'


def max_price(bot, update, user_data):
    maxprice = update.message.text
    user_data[update.message.chat["username"]][search_id]['max_price'] = maxprice
    text = ('Thank you, i am starting a search for you.\n'
            f'Your currency: {user_data[update.message.chat["username"]][search_id]["currency"]}'
            f'\nCity: {user_data[update.message.chat["username"]][search_id]["city"]}'
            f'\nCheck in date: {user_data[update.message.chat["username"]][search_id]["check_in"]}\n'
            f'Check out date: {user_data[update.message.chat["username"]][search_id]["check_out"]}'
            f'\nNumber of guests: {user_data[update.message.chat["username"]][search_id]["adult"]}\n'
            f'Room type: {", ".join(user_data[update.message.chat["username"]][search_id]["room_type"])}'
            f'\nMaximum price: {user_data[update.message.chat["username"]][search_id]["max_price"]}'
            )
    print(user_data)
    update.message.reply_text(text)
    search_home(bot, update, user_data)
    return ConversationHandler.END


def search_home(bot, update, user_data):
    api = airbnb.Api(randomize=True, currency=user_data[update.message.chat["username"]][search_id]["currency"])
    print(user_data)
    homes = api.get_homes(query=user_data[update.message.chat["username"]][search_id]['city'],
                          adults=user_data[update.message.chat["username"]][search_id]["adult"],
                          price_max=user_data[update.message.chat["username"]][search_id]["max_price"],
                          checkin=user_data[update.message.chat["username"]][search_id]["check_in"],
                          checkout=user_data[update.message.chat["username"]][search_id]["check_out"],
                          room_types=user_data[update.message.chat["username"]][search_id]["room_type"])

    with open(f'@{update.message.chat["username"]}' +
              f'{user_data[update.message.chat["username"]][search_id]["search_id"]}'+'.json', 'w') as file:
        json.dump(homes, file)


def help_comm(bot, update, user_data):
    text = '''What does this bot do?\n
Tracks prices for apartments that suits your criteria, when it founds new offer bot sends you picture, price and link to this offer.\n
You should set your currency, check in and check out dates, number of guests, city name, room types, minimum and maximum price per night.\n
How to use?
1.To make first search subscription go to menu and then press "New search".\n
2.Set all required parameters.\n
3. Press save, now you made your first subscription.\n
To change or delete parameters go to menu and press "edit".
To show all of your subscriptions go to menu and press "my subscriptions".
    '''
    update.message.reply_text(text)


def my_subs(bot, update, user_data):
    text = 'Здесь должны быть существующие подписки'
    update.message.reply_text(text)

