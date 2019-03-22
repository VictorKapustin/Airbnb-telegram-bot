from sqlalchemy import create_engine
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from DB.models import User, Subscription, ListingId
import logging
import settings
from datetime import datetime

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
DBSession = sessionmaker(bind=engine)
session = DBSession()


def add_listings(listings, subscription_id):
    """
    add known listings to 'listing' table in Database
    :param listings: array of listings from user_data['available_listings']
    :param subscription_id: id of subscription for these listings
    :return:
    """
    for listing in listings:
        new_listing = ListingId(listing_id=listing,
                                subscription=subscription_id)
        session.add(new_listing)
    session.commit()

def user_in_db(telegram_id):
    """
    Check if user already in Database
    :param telegram_id: user's id
    :return: True if user in Databse, else False
    """
    sel = select([User]).where(User.telegram_id == telegram_id)
    result = session.execute(sel)
    return bool(result.first())


def add_new_user(chat):
    """
    Add new user into Database
    :param chat: update.message.chat
    """
    sel = select([User]).where(User.telegram_id == chat["id"])
    result = session.execute(sel)
    if not result.first():
        new_user = User(telegram_id=chat["id"], first_name=chat['first_name'], last_name=chat['last_name'],
                        username=chat['username'])
        session.add(new_user)
        session.commit()


def add_new_subscription(telegram_id, user_data):
    """
    Add new subscription into Database
    :param telegram_id: user's id
    :param user_data: subscription's data
    :return:
    """
    logging.info("Add subscription new in DB")
    new_subscription = Subscription(telegram_id=telegram_id,
                                    check_in=datetime.strptime(user_data["check_in"], "%Y-%m-%d"),
                                    check_out=datetime.strptime(user_data["check_out"], "%Y-%m-%d"),
                                    city=user_data["city"], currency=user_data["currency"],
                                    max_price=user_data["max_price"],
                                    adults=user_data['adults'],
                                    room_type=user_data["room_type"])
    session.add(new_subscription)
    session.commit()
    return new_subscription.id
