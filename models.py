from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)          # private, group, supergroup, channel
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat")

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="user")
    reactions = relationship("Reaction", back_populates="user")

class Message(Base):
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    edited_date = Column(DateTime, nullable=True)
    reply_to_message_id = Column(BigInteger, nullable=True)
    forward_from = Column(JSON, nullable=True)
    media = Column(JSON, nullable=True)                # список словарей с информацией о файлах
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_messages_chat_date', 'chat_id', 'date'),
        Index('ix_messages_user', 'user_id'),
    )

class Reaction(Base):
    __tablename__ = 'reactions'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reaction = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', 'reaction', name='uq_message_user_reaction'),
    )