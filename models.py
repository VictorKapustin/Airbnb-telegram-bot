from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(String(25), primary_key=True)
    first_name = Column(String(25))
    last_name = Column(String(25))
    username = Column(String(25))
    subscriptions = relationship("Subscription", backref="subscripions")


class Subscription(Base):
    __tablename__ = 'subscription'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(25), ForeignKey('user.telegram_id'))
    check_in = Column(DateTime)
    city = Column(String(25))
    currency = Column(String(3))
    max_price = Column(DECIMAL)


if __name__ == "__main__":
    e = create_engine("sqlite:///user_subs.db")
    engine = create_engine("sqlite:///user_subs.db")
    Base.metadata.create_all(engine)

