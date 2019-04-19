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
                                    check_in=user_data["check_in"],
                                    check_out=user_data["check_out"],
                                    city=user_data["city"], currency=user_data["currency"],
                                    max_price=user_data["max_price"],
                                    adults=user_data['adults'],
                                    room_type=user_data["room_type"])
    session.add(new_subscription)
    session.commit()
    return new_subscription.id


def get_my_subscriptions(telegram_id):
    subs = []
    for sub in session.query(Subscription).filter(Subscription.telegram_id == telegram_id).all():
        subs.append([sub.city, sub.check_in, sub.check_out,
                     sub.room_type, sub.max_price, sub.id])
    return subs


def get_subscription_by_id(sub_id):
    sub = session.query(Subscription).filter(Subscription.id == sub_id).first()
    return [sub.city, sub.check_in, sub.check_out, sub.room_type, sub.max_price, sub.id]


def delete_subcription(sub_id):
    session.query(ListingId).filter_by(subscription=sub_id).delete()
    session.query(Subscription).filter_by(id=sub_id).delete()
    session.commit()


def get_all_subs():
    subs = []
    for sub in session.query(Subscription).all():
        subs.append(
            [sub.currency, sub.city, sub.adults, sub.max_price, sub.check_in, sub.check_out, sub.room_type, sub.id,
             sub.telegram_id])
    return subs


def find_new_listings(list_of_listings, sub_id):
    known_listings = set()
    for listing in session.query(ListingId).filter_by(subscription=sub_id).all():
        known_listings.add(listing.listing_id)
    unknown_listings = list_of_listings.difference(known_listings)
    print(known_listings)
    print(len(known_listings))
    print(unknown_listings)
    print(len(unknown_listings))
    return unknown_listings
