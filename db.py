import datetime, hashlib
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from flask_login import UserMixin

engine = create_engine("sqlite:///game.db", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base, UserMixin):      # ← наследуем от UserMixin
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    mmr = Column(Integer, default=1000)
    created = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()

def _hash(p):
    return hashlib.sha256(p.encode()).hexdigest()

def add_user(u, p):
    db = get_session()
    db.add(User(username=u, password_hash=_hash(p)))
    db.commit()

def verify_user(u, p):
    db = get_session()
    obj = db.query(User).filter_by(username=u).first()
    return obj and obj.password_hash == _hash(p)
