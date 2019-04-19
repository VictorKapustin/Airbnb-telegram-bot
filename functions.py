import requests
import re
import logging
import airbnb
import arrow
import json
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

from DB.db_methods import add_listings, add_new_subscription, add_new_user, user_in_db, get_my_subscriptions
from DB.db_methods import get_subscription_by_id, delete_subcription, get_all_subs, find_new_listings
from texts import greeting, help_text, thank_text
from settings import web_url
from DB.db_methods import session
from DB.models import ListingId

INLINE = 'inline'


def keys(buttons):
    """
    compile inline keyboard
    :param buttons: list of dictionaries, every dictionary is row of buttons
    :return:
    """
    keyboard = []
    for row_count, row in enumerate(buttons):
        keyboard.append([])
        for key, value in row.items():
            keyboard[row_count].append(
                InlineKeyboardButton(key, callback_data=value))
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def greet_user(bot, update, user_data):
    buttons = [
        {'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    try:
        update.message.reply_text(greeting, reply_markup=keys(buttons))
    except AttributeError:
        bot.send_message(chat_id=update.callback_query.message.chat.id,
                         text=greeting, reply_markup=keys(buttons))
    if not user_in_db(update.message.chat["id"]):
        add_new_user(update.message.chat)
    return INLINE


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
                 'Edit': my_subs,
                 'day': stay_days,
                 'subscription_id': choose_subscription,
                 'Delete_subscription': delete_subscription,
                 'month': choose_day_checkin,
                 'checkin': write_check_in}

    return functions.get(command[0])(bot, update, user_data)


def delete_subscription(bot, update, user_data):
    sub_id = update.callback_query.data.split(';')[1]
    delete_subcription(sub_id)
    text = 'This subscription was deleted'
    query = update.callback_query
    buttons = [
        {'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


def choose_subscription(bot, update, user_data):
    sub_id = update.callback_query.data.split(';')[1]
    your_subscription = get_subscription_by_id(sub_id)
    text = f'please choose what to do with this subscription \n{your_subscription}'
    buttons = [{'Menu': 'Menu', 'Delete': f'Delete_subscription;{sub_id}'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


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
    text = "Do you want to add new search or delete existing?"
    buttons = [{'New search': 'New search', 'Delete existing search': 'Edit'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


def help_comm(bot, update, user_data):
    buttons = [
        {'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    query = update.callback_query
    query.edit_message_text(help_text, reply_markup=keys(buttons))
    return INLINE


def my_subs(bot, update, user_data):
    buttons = [
        {'Menu': 'Menu', 'My subscriptions': 'My subscriptions'}, {'Help': 'Help'}]
    query = update.callback_query
    subs = get_my_subscriptions(query.message.chat.id)
    text = 'City              check in              check out              room type              price'
    for subscription in subs:
        subscription_button = {}
        subscription_button[
            f'{subscription[0]}, {subscription[1][:11]}, {subscription[2][:11]}, {subscription[3]}, '
            f'{subscription[4]}'] = f'subscription_id;{subscription[5]}'
        buttons.insert(0, subscription_button)
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


def new_search(bot, update, user_data):
    query = update.callback_query
    logging.info(
        f'@{query["message"]["chat"]["username"]} started new subscription')
    text = "Ok, now please choose your currency"
    buttons = [{'USD$': 'Curr;USD', 'EUR€': 'Curr;EUR'},
               {'RUB₽': 'Curr;RUB', 'GBP£': 'Curr;GBP'}]
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


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
        return choose_month(bot, update, user_data)
    else:
        text = 'Please write city name in English'
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return 'city'


def choose_month(bot, update, user_data):
    text = 'Choose month of check in?'
    buttons = [{}, {}, {}, {}]
    months_count = 0
    now = arrow.utcnow()
    for row in buttons:
        for month in range(2):
            row[str(now.shift(months=+months_count).format('MMMM'))] = 'month;' + \
                str(now.shift(months=+months_count).format('YYYY-MM'))
            months_count += 1
    update.message.reply_text(text, reply_markup=keys(buttons))
    return INLINE


def choose_day_checkin(bot, update, user_data):
    year_month = update.callback_query.data.split(';')[1]
    print_date = arrow.get(year_month, "YYYY-MM").format("MMMM YYYY")
    text = f'Choose day in {print_date} to check in?'
    buttons = [{}, {}, {}, {}, {}]
    day = 1
    br = 0
    for row in buttons:
        for day_number in range(7):
            row[str(day)] = 'checkin;' + year_month + '-' + str(day)
            if year_month != arrow.get(year_month, "YYYY-MM").shift(days=+day).format("YYYY-MM"):
                br = 1
                break
            day += 1
        if br:
            break
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


def write_check_in(bot, update, user_data):
    checkin = update.callback_query.data.split(';')[1]
    print(checkin)
    user_data['check_in'] = checkin
    return ask_for_check_out(bot, update, user_data)


def ask_for_check_out(bot, update, user_data):
    text = 'How many days would you like stay?'
    buttons = [{}, {}, {}, {}]
    day = 1
    for row in buttons:
        for day_number in range(6):
            row[str(day)] = 'day;'+str(day)
            day += 1
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


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
    return INLINE


def choose_room(bot, update, user_data):
    text = 'Choose room type'
    buttons = [{'Entire home/apt': 'Room;Entire home/apt'},
               {'Private room': 'Room;Private room'},
               {'Shared room': 'Room;Shared room'}]
    query = update.callback_query
    query.edit_message_text(text, reply_markup=keys(buttons))
    return INLINE


def add_room(bot, update, user_data):
    room = update.callback_query.data.split(';')[1]
    user_data['room_type'] = room
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
            f'Room type: {user_data["room_type"]}'
            f'\nMaximum price: {user_data["max_price"]}'
            )
    buttons = [{'Save': 'Save', 'Edit': 'Edit'}]
    update.message.reply_text(text, reply_markup=keys(buttons))

    return INLINE


def bd_write_subscription(query, user_data):
    sub_id = add_new_subscription(query['message']['chat']["id"], user_data)
    add_listings(user_data['available_listings'], sub_id)


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
            try:
                listings = homes['explore_tabs'][0]["sections"][1]['listings']
            except KeyError:
                text = "Sorry we could't process your request, please try again"
                query.edit_message_text(text)
                return greet_user(bot, update, user_data)
        except IndexError:
            try:
                listings = homes['explore_tabs'][0]["sections"][0]['listings']
            except KeyError:
                text = "Sorry we could't process your request, please try again"
                query.edit_message_text(text)
                return greet_user(bot, update, user_data)

        for listing in listings:
            user_data['available_listings'].append(listing["listing"]["id"])

        has_next_page = homes['explore_tabs'][0]['pagination_metadata']['has_next_page']
        try:
            items_offset = homes['explore_tabs'][0]['pagination_metadata']['items_offset']
        except KeyError:
            print('no next page')

    if len(user_data['available_listings']) < 200:
        bd_write_subscription(query, user_data)
        text = thank_text
    else:
        text = f'We have found {len(user_data["available_listings"])} offers for your criteria, this is too much,' \
            f'you can see these offers by pressing button bellow, but your subscription will not be added to our ' \
            f'database. If you still want to add subscription and get new offers, please tighten your search, ' \
            f'set lower price for example'

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
    keyboard = [[InlineKeyboardButton(
        'Go to Airbnb', callback_data='url', url=f'{give_url.url}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup)


def get_listings(bot, job):
    print('started scan new listing')
    list_of_subs = get_all_subs()
    for sub in list_of_subs:
        items_offset = 0
        actual_listings = set()
        has_next_page = True
        api = airbnb.Api(randomize=True, currency=sub[0])
        while has_next_page:
            homes = api.get_homes(query=sub[1],
                                  adults=sub[2],
                                  price_max=sub[3],
                                  checkin=sub[4][:10],
                                  checkout=sub[5][:10],
                                  room_types=sub[6],
                                  offset=items_offset)  # Отступ объявлений

            try:
                try:
                    listings = homes['explore_tabs'][0]["sections"][1]['listings']
                except KeyError:
                    logging.info(
                        f'Have a KeyError on {sub[7]} subscription while trying to get new listings')
            except IndexError:
                try:
                    listings = homes['explore_tabs'][0]["sections"][0]['listings']
                except KeyError:
                    logging.info(
                        f'Have a KeyError on {sub[7]} subscription while trying to get new listings')

            for listing in listings:
                actual_listings.add(listing["listing"]["id"])

            has_next_page = homes['explore_tabs'][0]['pagination_metadata']['has_next_page']
            try:
                items_offset = homes['explore_tabs'][0]['pagination_metadata']['items_offset']
            except KeyError:
                print('no next page while scanning for new listings')
        print('actual', actual_listings)
        print(len(actual_listings))
        new_listings = find_new_listings(actual_listings, sub[7])
        send_notification(new_listings, sub, bot)


def send_notification(new_listings, parameters, bot):
    for listing_id in new_listings:

        url = f'https://www.airbnb.com/rooms/{listing_id}?guests={parameters[2]}&' \
            f'adults={parameters[2]}&check_in={parameters[4][:10]}&check_out={parameters[5][:10]}'
        api = airbnb.Api(randomize=True, currency=parameters[0])
        details = api.get_listing_details(listing_id)
        text = 'Hello, we have found new home for you:' \
               f''
        picture = details["pdp_listing_detail"]["photos"][0]["large"]

        keyboard = [[InlineKeyboardButton(
            'See listing', callback_data='url', url=f'{url}')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_photo(
            chat_id=parameters[8], photo=picture, caption=text, reply_markup=reply_markup)
        new_listing = ListingId(listing_id=listing_id,
                                subscription=parameters[7])
        session.add(new_listing)
    session.commit()
