from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import uuid
import bcrypt
import json
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    @staticmethod
    def generate_user_id():
        return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = 'conversation'
    
    conversation_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('user.user_id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_conversation_id():
        return str(uuid.uuid4())

class Message(Base):
    __tablename__ = 'message'
    
    message_id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey('conversation.conversation_id'), nullable=False)
    message_content = Column(Text, nullable=False)
    response_message = Column(Text)
    message_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    @staticmethod
    def generate_message_id():
        return str(uuid.uuid4())

class Setting(Base):
    __tablename__ = 'settings'
    
    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    setting_name = Column(String, nullable=False)
    setting_sub = Column(String)

def init_db():
    with open('settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    db_name = settings['database']['name']
    db_path = os.path.join('database', db_name)
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    if not session.query(User).filter_by(username='admin').first():
        admin_user = User(
            user_id=User.generate_user_id(),
            username='admin',
            password=User.hash_password('admin123'),
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True,
            is_verified=True
        )
        session.add(admin_user)
        
        default_conversation = Conversation(
            conversation_id=Conversation.generate_conversation_id(),
            user_id=admin_user.user_id,
            name='Yeni Sohbet 1'
        )
        session.add(default_conversation)
        
        welcome_message = Message(
            message_id=Message.generate_message_id(),
            conversation_id=default_conversation.conversation_id,
            message_content="Merhaba! DinamikChat'e hoş geldiniz.",
            response_message="Merhaba! Size nasıl yardımcı olabilirim?"
        )
        session.add(welcome_message)
        
        for mode, prompt in settings['ui']['modes'].items():
            setting = Setting(
                setting_name=mode,
                setting_sub=prompt
            )
            session.add(setting)
        
        session.commit()
    
    session.close()
    
    return engine

def get_db_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session() 