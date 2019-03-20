import json
import logging
from datetime import datetime
import arrow
import re
from settings import web_url
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
import airbnb
import requests
from texts import greeting, help_text, thank_text, reduce_price
import time
from DB.db_methods import *
inline = 'inline'


def keys(buttons):
    """
    compile inline keyboard
    :param buttons: list of dictionaries, every dictionary is row of buttons
    :return:
    """
    keyboard = []
    row_count = 0
    for row in buttons:
        keyboard.append([])
        for key, value in row.items():
            keyboard[row_count].append(InlineKeyboardButton(key, callback_data=value))
        row_count += 1
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def greet_user(bot, update, user_data):
    buttons = [{'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    update.message.reply_text(greeting, reply_markup=keys(buttons))
    if not user_in_db(update.message.chat["id"]):
        add_new_user(update.message.chat)
    return inline


def main_menu(bot, update, user_data):
    command = update.callback_query.data.split(';')
    functions = {'Menu': menu,
                 'Help': help_comm,
                 'My subscriptions': my_subs,
                 'New search': new_search,
                 'Curr': currency,
                 'Adults': adults,
                 'Room': add_room,
                 'Save': search_home,  # через раз выбрасывает ошибку
                 'Edit': edit,
                 'day': stay_days}

    return functions.get(command[0])(bot, update, user_data)


def edit(bot, update, user_data):
    pass


def currency(bot, update, user_data):
    curr = update.callback_query.data.split(';')[1]
    user_data['currency'] = curr
    return get_city(bot, update, user_data)


def adults(bot, update, user_data):
    adult = update.callback_query.data.split(';')[1]
    user_data['adults'] = adult
    return choose_room(bot, update, user_data)


def menu(bot, update, user_data):
    text = "Do you want to add new search or edit existing?"
    buttons = [{'New search': 'New search', 'Edit existing search': 'Edit existing search'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return inline


def help_comm(bot, update, user_data):
    buttons = [{'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    query = update.callback_query
    query.edit_message_text(help_text, reply_markup=keys(buttons))
    return inline


def my_subs(bot, update, user_data):
    text = 'Здесь должны быть существующие подписки'
    buttons = [{'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return inline


def new_search(bot, update, user_data):
    bot.search_id += 1
    user_data['search_id'] = str(bot.search_id)
    query = update.callback_query
    logging.info(f'@{query["message"]["chat"]["username"]} started new subscription')
    text = "Ok, now please choose your currency"
    buttons = [{'USD$': 'Curr;USD', 'EUR€': 'Curr;EUR'}, {'RUB₽': 'Curr;RUB', 'GBP£': 'Curr;GBP'}]
    query.edit_message_text(text, reply_markup=keys(buttons))
    return inline


def get_city(bot, update, user_data):
    text = 'ok, now write city name where you want to go'
    query = update.callback_query
    query.edit_message_text(text)
    return 'city'


def set_city(bot, update, user_data):
    city = update.message.text
    template = '[a-zA-Z\s-]*'
    # '*'=Любое количество символов, '\s'=space, '-' должен идти последним или первым
    match = re.fullmatch(template, city)
    if len(city) < 2:
        text = ('Sorry, you entered wrong city, length of city name should be longer than 2 letters, ' +
                'now write city name where you want to go')
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'
    elif match:
        user_data['city'] = city
        return ask_for_check_in(bot, update, user_data)
    else:
        text = 'Please write city name in English'
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'


def ask_for_check_in(bot, update, user_data):
    text = 'When do you want to check in? Date format: YYYY-MM-DD'
    update.message.reply_text(text)
    return 'checkin'


def checkin(bot, update, user_data):
    check_in = update.message.text
    template = '\d{4}-\d\d-\d\d'
    match = re.fullmatch(template, check_in)
    if match:
        date = arrow.get(check_in)
        if date > arrow.utcnow():
            user_data['check_in'] = check_in
            return ask_for_check_out(bot, update, user_data)
        else:
            text = 'Your date is in the past, please enter date in future, format: YYYY-MM-DD'
            update.message.reply_text(text)
            return 'checkin'
    else:
        text = 'Your date is incorrect, please enter date in format YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkin'


def ask_for_check_out(bot, update, user_data):
    text = 'How many days would you like stay?'
    buttons = [{}, {}, {}, {}]
    day = 1
    for row in buttons:
        for i in range(6):
            row[str(day)] = 'day;'+str(day)
            day += 1
    update.message.reply_text(text, reply_markup=keys(buttons))
    return inline


def stay_days(bot, update, user_data):
    days = update.callback_query.data.split(';')[1]
    check_in = arrow.get(user_data['check_in'])
    check_out = str(check_in.replace(days=int(days)).date())
    user_data['check_out'] = check_out
    return ask_for_guests_number(bot, update, user_data)



def ask_for_guests_number(bot, update, user_data):
        text = 'How many guests?'
        buttons = [{'1': 'Adults;1', '2': 'Adults;2', '3': 'Adults;3'},
                  {'4': 'Adults;4', '5': 'Adults;5', '6': 'Adults;6'}]
        query = update.callback_query
        query.edit_message_text(text, reply_markup=keys(buttons))
        return inline



def choose_room(bot, update, user_data):
    text = 'Choose room type'
    buttons = [{'Entire home/apt': 'Room;Entire home/apt'},
               {'Private room': 'Room;Private room'},
               {'Shared room': 'Room;Shared room'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return inline


def add_room(bot, update, user_data):
    room = update.callback_query.data.split(';')[1]
    user_data['room_type'] = [room]
    text = "What is your maximum price per night? Only digits"
    query = update.callback_query
    query.edit_message_text(text)
    return 'maxprice'


def max_price(bot, update, user_data):
    maxprice = update.message.text
    user_data['max_price'] = maxprice
    text = ('Please check your criteria, do you want to save them and start search?\n'
            f'Your currency: {user_data["currency"]}'
            f'\nCity: {user_data["city"]}'
            f'\nCheck in date: {user_data["check_in"]}\n'
            f'Check out date: {user_data["check_out"]}'
            f'\nNumber of guests: {user_data["adults"]}\n'
            f'Room type: {", ".join(user_data["room_type"])}'
            f'\nMaximum price: {user_data["max_price"]}'
            )
    buttons = [{'Save': 'Save', 'Edit': 'Edit'}]
    update.message.reply_text(text, reply_markup=keys(buttons))
    add_new_subscription(update.message.chat["id"], user_data)
    return inline


def search_home(bot, update, user_data):
    query = update.callback_query
    user_data['available_listings'] = []
    items_offset = 0
    has_next_page = True
    api = airbnb.Api(randomize=True, currency=user_data["currency"])
    while has_next_page:
        homes = api.get_homes(query=user_data['city'],
                              adults=user_data["adults"],
                              price_max=user_data["max_price"],
                              checkin=user_data["check_in"],
                              checkout=user_data["check_out"],
                              room_types=user_data["room_type"],
                              offset=items_offset)  # Отступ объявлений

        try:
            listings = homes['explore_tabs'][0]["sections"][1]['listings']
        except(IndexError):
            listings = homes['explore_tabs'][0]["sections"][0]['listings']

        for listing in listings:
            user_data['available_listings'].append(listing["listing"]["id"])

        has_next_page = homes['explore_tabs'][0]['pagination_metadata']['has_next_page']
        try:
            items_offset = homes['explore_tabs'][0]['pagination_metadata']['items_offset']
        except KeyError:
            print('no next page')

    print(user_data)
    print(len(set(user_data['available_listings'])))
    text = thank_text
    params = {  # Ссылка для выдачи на веб на существующие варианты
        'query': user_data['city'],
        'adults': user_data["adults"],
        'children': '0',
        'price_min': '0',
        'price_max': user_data["max_price"],
        'checkin': user_data["check_in"],
        'checkout': user_data["check_out"],
        'room_types[]': user_data["room_type"],
        'refinement_paths[]': '/homes',
        'display_currency': user_data["currency"]
    }

    give_url = requests.get(web_url, params=params)
    keyboard = [[InlineKeyboardButton('Go to Airbnb', callback_data='url', url=f'{give_url.url}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup)


