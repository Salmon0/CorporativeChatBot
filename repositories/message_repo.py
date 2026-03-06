from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List
from models import Chat, User, Message, Reaction
from dto import ChatDTO, UserDTO, MessageDTO, ReactionDTO

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- Чаты ----------
    async def get_or_create_chat(self, chat_dto: ChatDTO) -> Chat:
        stmt = select(Chat).where(Chat.id == chat_dto.id)
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()
        if not chat:
            chat = Chat(
                id=chat_dto.id,
                title=chat_dto.title,
                type=chat_dto.type
            )
            self.session.add(chat)
            await self.session.flush()
        return chat

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        stmt = select(Chat).where(Chat.id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- Пользователи ----------
    async def get_or_create_user(self, user_dto: UserDTO) -> User:
        stmt = select(User).where(User.id == user_dto.id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=user_dto.id,
                username=user_dto.username,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name
            )
            self.session.add(user)
            await self.session.flush()
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- Сообщения ----------
    async def save_message(self, message_dto: MessageDTO) -> Message:
        # Убеждаемся, что чат существует
        await self.get_or_create_chat(message_dto.chat)
        if message_dto.user:
            await self.get_or_create_user(message_dto.user)

        stmt = select(Message).where(
            Message.id == message_dto.id,
            Message.chat_id == message_dto.chat.id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.edited_date = message_dto.edited_date or existing.edited_date
            return existing

        message = Message(
            id=message_dto.id,
            chat_id=message_dto.chat.id,
            user_id=message_dto.user.id if message_dto.user else None,
            text=message_dto.text,
            date=message_dto.date,
            edited_date=message_dto.edited_date,
            reply_to_message_id=message_dto.reply_to_message_id,
            forward_from=message_dto.forward_from,
            media=message_dto.media
        )
        self.session.add(message)
        await self.session.flush()

        for reaction_dto in message_dto.reactions:
            await self.save_reaction(reaction_dto)

        return message

    async def save_reaction(self, reaction_dto: ReactionDTO) -> Reaction:
        stmt = select(Reaction).where(
            Reaction.message_id == reaction_dto.message_id,
            Reaction.user_id == reaction_dto.user_id,
            Reaction.reaction == reaction_dto.reaction
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        reaction = Reaction(
            message_id=reaction_dto.message_id,
            user_id=reaction_dto.user_id,
            reaction=reaction_dto.reaction,
            date=reaction_dto.date or datetime.utcnow()
        )
        self.session.add(reaction)
        await self.session.flush()
        return reaction

    async def get_messages(
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(
                Message.chat_id == chat_id,
                Message.date >= start_date,
                Message.date <= end_date
            )
            .options(selectinload(Message.user), selectinload(Message.reactions))
            .order_by(Message.date)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_messages(self, chat_id: int, start_date: datetime, end_date: datetime) -> int:
        stmt = select(func.count(Message.id)).where(
            Message.chat_id == chat_id,
            Message.date >= start_date,
            Message.date <= end_date
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_message_by_id(self, chat_id: int, message_id: int) -> Optional[Message]:
        stmt = select(Message).where(
            Message.chat_id == chat_id,
            Message.id == message_id
        ).options(selectinload(Message.user), selectinload(Message.reactions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()