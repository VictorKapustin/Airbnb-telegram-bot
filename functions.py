import json
import logging
from datetime import datetime
import re
from settings import web_url
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
import airbnb
import requests

search_id = 0
inline = 'inline'

def greet_user(bot, update, user_data):
    text = ("Hi! I'm bot low cost offers finder at Airbnb.\n\n"
            "I will follow your filters and tell you when i find new offer for you.\n\n"
            "It's simple to use me:\n"
            " · Press Menu, to add your first notification or to edit existing\n"
            " · To read full description of bot functions press Help button")

    keyboard = [[InlineKeyboardButton("Menu", callback_data='Menu'),
                 InlineKeyboardButton("My subscriptions", callback_data='My subscriptions')],

                [InlineKeyboardButton("Help", callback_data='Help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text, reply_markup=reply_markup)
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
                 'Save': search_home,
                 'Edit': edit}

    return functions[command[0]](bot, update, user_data)


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

    keyboard = [[InlineKeyboardButton('New search', callback_data='New search'),
                 InlineKeyboardButton('Edit existing search', callback_data='Edit existing search')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query

    query.edit_message_text(text, reply_markup=reply_markup)
    return inline


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
    keyboard = [[InlineKeyboardButton("Menu", callback_data='Menu'),
                 InlineKeyboardButton("My subscriptions", callback_data='My subscriptions')],
                [InlineKeyboardButton("Help", callback_data='Help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.edit_message_text(text, reply_markup=reply_markup)
    return inline


def my_subs(bot, update, user_data):
    text = 'Здесь должны быть существующие подписки'
    keyboard = [[InlineKeyboardButton("Menu", callback_data='Menu'),
                 InlineKeyboardButton("My subscriptions", callback_data='My subscriptions')],
                [InlineKeyboardButton("Help", callback_data='Help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.edit_message_text(text, reply_markup=reply_markup)
    return inline


def new_search(bot, update, user_data):
    global search_id
    search_id += 1
    user_data['search_id'] = str(search_id)
    logging.info(f'@{update.callback_query.message["username"]} started new subscription')
    text = "Ok, now please choose your currency"
    keyboard = [[InlineKeyboardButton('USD$', callback_data='Curr;USD'),
                 InlineKeyboardButton('EUR€', callback_data='Curr;EUR')],
                [InlineKeyboardButton('RUB₽', callback_data='Curr;RUB'),
                 InlineKeyboardButton('GBP£', callback_data='Curr;GBP')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.edit_message_text(text, reply_markup=reply_markup)
    return inline


def get_city(bot, update, user_data):
    text = 'ok, now write city name where you want to go'
    query = update.callback_query
    query.edit_message_text(text)
    return 'city'


def set_city(bot, update, user_data):
    city = update.message.text
    template = r'[a-zA-Z\s-]*'
    # '*'=Любое количество символов, '\s'=space, '-' должен идти последним или первым
    match = re.fullmatch(template, city)
    if len(city) < 2:
        text = ('Sorry, you entered wrong city, length of city name should be longer than 2 letters, ' +
                'now write city name where you want to go')
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'
    elif match:
        user_data['city'] = city
        text = 'When do you want to check in? Date format: YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkin'
    else:
        text = 'Please write city name in English'
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'


def checkin(bot, update, user_data):
    check_in = update.message.text
    template = r'\d{4}-\d\d-\d\d'
    match = re.fullmatch(template, check_in)

    if match:
        date = datetime.strptime(check_in, '%Y-%m-%d')
        if date > datetime.now():
            user_data['check_in'] = check_in
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
        check_in = datetime.strptime(user_data['check_in'], '%Y-%m-%d')
        if check_in < date:
            user_data['check_out'] = check_out
            text = 'How many guests?'
            keyboard = [[InlineKeyboardButton('1', callback_data='Adults;1'),
                         InlineKeyboardButton('2', callback_data='Adults;2'),
                         InlineKeyboardButton('3', callback_data='Adults;3')],

                        [InlineKeyboardButton('4', callback_data='Adults;4'),
                         InlineKeyboardButton('5', callback_data='Adults;5'),
                         InlineKeyboardButton('6', callback_data='Adults;6')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text, reply_markup=reply_markup)
            return inline
        else:
            text = 'Your date of checkout is earlier than check in, please enter valid date, format: YYYY-MM-DD'
            update.message.reply_text(text)
            return 'checkout'
    else:
        text = 'Your date is incorrect, please enter date in format YYYY-MM-DD'
        update.message.reply_text(text)
        return 'checkout'


def choose_room(bot, update, user_data):
    text = 'Choose room type'
    keyboard = [[InlineKeyboardButton('Entire home/apt', callback_data='Room;Entire home/apt')],
                [InlineKeyboardButton('Private room', callback_data='Room;Private room')],
                [InlineKeyboardButton('Shared room', callback_data='Room;Shared room')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.edit_message_text(text, reply_markup=reply_markup)
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
    keyboard = [[InlineKeyboardButton('Save', callback_data='Save'),
                 InlineKeyboardButton('Edit', callback_data='Edit')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text, reply_markup=reply_markup)
    return inline


def save_start(bot, update, user_data):
    search_home(bot, update, user_data)



def search_home(bot, update, user_data):
    """
    Надо выполнить поиск на данный момент, получить список id листингов,
    выдать ссылку на существующие варианты, добавить в бд все данные
    """
    api = airbnb.Api(randomize=True, currency=user_data["currency"])
    homes = api.get_homes(query=user_data['city'],
                          adults=user_data["adults"],
                          price_max=user_data["max_price"],
                          checkin=user_data["check_in"],
                          checkout=user_data["check_out"],
                          room_types=user_data["room_type"])
    print(homes['explore_tabs'][0]["sections"]) #[0]["sections"][1]["listings"]["listing"]["id"]
    # тут происходит ошибка индекса через раз

    params = {  # Ссылка для выдачи на веб на существующие варианты
        'query': user_data['city'],
        'adults': user_data["adults"],
        'children': '0',
        'price_min': '0',
        'price_max': user_data["max_price"],
        'checkin': user_data["check_in"],
        'checkout': user_data["check_out"],
        'room_types[]': user_data["room_type"],  # ['Entire home/apt', 'Private room', 'Shared room']
        'refinement_paths[]': '/homes',
        'display_currency': user_data["currency"]
    }

    give_url = requests.get(web_url, params=params)

    text = 'Thank you, we added your subscription and started to track it, ' \
           'by pressing button bellow you will go to airbnb website and get ' \
           'existing listings for your search and we will notify you about new offers'

    keyboard = [[InlineKeyboardButton('Go to Airbnb', callback_data='url', url=f'{give_url.url}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.edit_message_text(text, reply_markup=reply_markup)

    #return ConversationHandler.END


    # with open(f'@{update.message.chat["username"]}' +
    #           f'{user_data[search_id]["search_id"]}'+'.json', 'w') as file:
    #     json.dump(homes, file)




