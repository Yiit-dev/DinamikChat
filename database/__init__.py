import os
import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, create_engine, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    conversations = relationship("Conversation", back_populates="user")
    @staticmethod
    def generate_user_id():
        return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = 'conversation'
    conversation_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('user.user_id'))
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_archived = Column(Boolean, default=False)
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    @staticmethod
    def generate_conversation_id():
        return str(uuid.uuid4())

class Message(Base):
    __tablename__ = 'message'
    message_id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey('conversation.conversation_id'))
    message_content = Column(Text, nullable=False)
    response_message = Column(Text)
    message_date = Column(DateTime, default=datetime.datetime.now)
    sender = Column(String(10), default="user")
    conversation = relationship("Conversation", back_populates="messages")
    @staticmethod
    def generate_message_id():
        return str(uuid.uuid4())

class Database:
    def __init__(self):
        db_dir = 'database'
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_file = os.path.join(db_dir, 'dinamik_chat.db')
        self.engine = create_engine(f'sqlite:///{db_file}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    def get_user(self, username):
        return self.session.query(User).filter_by(username=username).first()
    def create_user(self, username, password, email, first_name, last_name):
        user = User(
            user_id=User.generate_user_id(),
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        self.session.add(user)
        self.session.commit()
        return user
    def get_conversations(self):
        return self.session.query(Conversation).order_by(Conversation.created_at.desc()).all()
    def create_conversation(self, name, user_id):
        conversation = Conversation(
            conversation_id=Conversation.generate_conversation_id(),
            name=name,
            user_id=user_id
        )
        self.session.add(conversation)
        self.session.commit()
        return conversation
    def update_conversation(self, conversation):
        self.session.commit()
    def delete_conversation(self, conversation):
        self.session.delete(conversation)
        self.session.commit()
    def get_messages(self, conversation_id):
        return self.session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.message_date).all()
    def create_message(self, conversation_id, content, sender="user", response=None):
        message = Message(
            message_id=Message.generate_message_id(),
            conversation_id=conversation_id,
            message_content=content,
            response_message=response,
            sender=sender
        )
        self.session.add(message)
        self.session.commit()
        return message
    def update_message(self, message):
        self.session.commit()
    def delete_message(self, message):
        self.session.delete(message)
        self.session.commit()

def create_db():
    db_dir = 'database'
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db_file = os.path.join(db_dir, 'dinamik_chat.db')
    engine = create_engine(f'sqlite:///{db_file}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    admin = session.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(
            user_id=User.generate_user_id(),
            username="admin",
            password="123",
            email="admin@dinamik.com",
            first_name="Admin",
            last_name="User",
            is_admin=True,
            is_verified=True
        )
        session.add(admin)
        session.commit()
    session.close()
    return engine

def get_db_session():
    db_file = os.path.join('database', 'dinamik_chat.db')
    engine = create_engine(f'sqlite:///{db_file}')
    Session = sessionmaker(bind=engine)
    return Session() 