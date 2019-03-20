from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import settings

 
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(String(25), primary_key=True)
    first_name = Column(String(25))
    last_name = Column(String(25))
    username = Column(String(25))

    def __repr__(self):
        return f"id:{self.telegram_id}\nusername: {self.username}"


class Subscription(Base):
    __tablename__ = 'subscription'
    telegram_id = Column(String(25), ForeignKey('user.telegram_id'))
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    city = Column(String(25))
    currency = Column(String(3))
    max_price = Column(DECIMAL)
    user = relationship("User", backref='subscriptions')

    def __repr__(self):
        return f"Subscription {self.id} for telegram id {self.telegram_id}"


if __name__ == "__main__":
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)

