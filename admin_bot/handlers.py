import logging
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import settings
from database import get_session
from repositories import MessageRepository
from . import export_utils
from dto import ChatDTO, UserDTO, MessageDTO

logger = logging.getLogger(__name__)

# ========== Команды администраторов ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для выгрузки корпоративных переписок.\n"
        "Используйте /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 Доступные команды:\n"
        "/start - приветствие\n"
        "/help - это сообщение\n"
        "/chats - показать список доступных чатов\n"
        "/export <чат> <период> – выгрузить сообщения за период (today, yesterday, week, month)\n"
        "/export <чат> <YYYY-MM-DD> <YYYY-MM-DD> – выгрузить за конкретные даты\n"
        "/status - статистика системы\n\n"
        "Чат может быть указан как числовой ID или @username (для публичных чатов)."
    )
    await update.message.reply_text(help_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Система работает. Статистика временно недоступна.")

# ========== Новая команда: список чатов ==========

async def chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех чатов, из которых есть сообщения."""
    async for session in get_session():
        repo = MessageRepository(session)
        # Получаем все чаты из БД (можно ограничить первыми 50)
        from models import Chat
        from sqlalchemy import select
        result = await session.execute(select(Chat).order_by(Chat.title).limit(50))
        chats = result.scalars().all()
        break

    if not chats:
        await update.message.reply_text("❌ Нет сохранённых чатов.")
        return

    keyboard = []
    for chat in chats:
        # Отображаем название чата (или ID, если нет названия)
        title = chat.title or str(chat.id)
        # Обрезаем слишком длинные названия
        if len(title) > 30:
            title = title[:27] + "..."
        callback_data = f"export_today:{chat.id}"
        keyboard.append([InlineKeyboardButton(title, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите чат для выгрузки сообщений за сегодня:",
        reply_markup=reply_markup
    )

# ========== Обработчик нажатий на кнопки ==========

async def handle_chat_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор чата из списка и запускает экспорт за сегодня."""
    query = update.callback_query
    await query.answer()  # обязательно ответить на callback

    # Извлекаем chat_id из callback_data
    data = query.data
    if not data.startswith("export_today:"):
        await query.edit_message_text("❌ Неизвестная команда.")
        return

    try:
        chat_id = int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Ошибка в идентификаторе чата.")
        return

    # Вычисляем период "сегодня" в UTC
    today = datetime.utcnow().date()
    start_date = datetime.combine(today, datetime.min.time())
    end_date = datetime.combine(today, datetime.max.time())

    # Запускаем экспорт (используем общую функцию)
    await perform_export(
        update=query,
        context=context,
        chat_id=chat_id,
        start_date=start_date,
        end_date=end_date,
        period_str="today"
    )

# ========== Общая функция экспорта ==========

async def perform_export(update, context, chat_id: int, start_date: datetime, end_date: datetime, period_str: str):
    """
    Универсальная функция экспорта сообщений.
    update может быть Message (для команд) или CallbackQuery (для кнопок).
    """
    # Определяем, откуда отправлять сообщения о прогрессе
    if hasattr(update, 'message') and update.message:
        # Пришло из команды /export
        message_obj = update.message
        reply_func = message_obj.reply_text
        edit_func = None
    else:
        # Пришло из callback
        query = update
        reply_func = query.message.reply_text
        edit_func = query.edit_message_text

    status_msg = await reply_func("🔄 Получаю данные из базы...")

    try:
        async for session in get_session():
            repo = MessageRepository(session)
            total = await repo.count_messages(chat_id, start_date, end_date)
            if total == 0:
                if edit_func:
                    await edit_func("❌ За указанный период сообщений не найдено.")
                else:
                    await status_msg.edit_text("❌ За указанный период сообщений не найдено.")
                return

            # Пагинация
            limit = 1000
            offset = 0
            all_messages = []
            if edit_func:
                await edit_func(f"🔄 Найдено {total} сообщений. Начинаю формировать файл...")
            else:
                await status_msg.edit_text(f"🔄 Найдено {total} сообщений. Начинаю формировать файл...")

            while True:
                messages = await repo.get_messages(chat_id, start_date, end_date, limit=limit, offset=offset)
                if not messages:
                    break
                all_messages.extend(messages)
                offset += limit
                if offset % (limit * 10) == 0:
                    progress = f"🔄 Обработано {offset} из {total}..."
                    if edit_func:
                        await edit_func(progress)
                    else:
                        await status_msg.edit_text(progress)
            break

        file_path = await export_utils.generate_csv(all_messages, chat_id, start_date, end_date)
        file_size = os.path.getsize(file_path)

        if file_size > 50 * 1024 * 1024:
            error_msg = "❌ Слишком много данных для одного файла (превышен лимит 50 МБ). Попробуйте сократить период."
            if edit_func:
                await edit_func(error_msg)
            else:
                await status_msg.edit_text(error_msg)
            os.unlink(file_path)
            return

        with open(file_path, 'rb') as f:
            await (update.message if hasattr(update, 'message') else update.message).reply_document(
                document=f,
                filename=f"export_{chat_id}_{period_str}.csv",
                caption=f"📊 Выгрузка сообщений из чата {chat_id} за {period_str}"
            )

        os.unlink(file_path)
        if edit_func:
            await edit_func("✅ Готово!")
        else:
            await status_msg.delete()

    except Exception as e:
        logger.exception("Ошибка при экспорте")
        error_msg = f"❌ Произошла ошибка: {e}"
        if edit_func:
            await edit_func(error_msg)
        else:
            await status_msg.edit_text(error_msg)

# ========== Существующая команда /export (переписываем с использованием perform_export) ==========

async def resolve_chat_id(context: ContextTypes.DEFAULT_TYPE, chat_identifier: str) -> int | None:
    try:
        return int(chat_identifier)
    except ValueError:
        try:
            chat = await context.bot.get_chat(chat_identifier)
            return chat.id
        except Exception as e:
            logger.error(f"Не удалось получить чат по username {chat_identifier}: {e}")
            return None

def parse_period(period_str: str) -> tuple[datetime, datetime] | None:
    today = datetime.utcnow().date()
    if period_str == 'today':
        start = end = today
    elif period_str == 'yesterday':
        start = end = today - timedelta(days=1)
    elif period_str == 'week':
        start = today - timedelta(days=7)
        end = today
    elif period_str == 'month':
        start = today.replace(day=1)
        end = today
    else:
        return None
    start_date = datetime.combine(start, datetime.min.time())
    end_date = datetime.combine(end, datetime.max.time())
    return start_date, end_date

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) not in (2, 3):
        await update.message.reply_text(
            "❌ Неверный формат. Используйте:\n"
            "/export <чат> <период> (today, yesterday, week, month)\n"
            "/export <чат> <YYYY-MM-DD> <YYYY-MM-DD>"
        )
        return

    chat_identifier = args[0]
    chat_id = await resolve_chat_id(context, chat_identifier)
    if not chat_id:
        await update.message.reply_text("❌ Не удалось определить чат. Проверьте ID или username.")
        return

    if len(args) == 2:
        period = args[1].lower()
        dates = parse_period(period)
        if not dates:
            await update.message.reply_text(
                "❌ Неверный период. Доступные: today, yesterday, week, month"
            )
            return
        start_date, end_date = dates
        period_str = period
    else:
        try:
            start_date = datetime.strptime(args[1], "%Y-%m-%d")
            end_date = datetime.strptime(args[2], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            period_str = f"{args[1]}_{args[2]}"
        except ValueError:
            await update.message.reply_text("❌ Неверный формат даты. Используйте YYYY-MM-DD")
            return

    # Используем общую функцию экспорта
    await perform_export(update, context, chat_id, start_date, end_date, period_str)

# ========== Обработчик входящих сообщений для сохранения (без изменений) ==========

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    if message.from_user and message.from_user.is_bot:
        return
    if message.text and message.text.startswith('/'):
        return

    chat = message.chat
    user = message.from_user

    chat_dto = ChatDTO(
        id=chat.id,
        title=chat.title,
        type=chat.type
    )

    user_dto = None
    if user and not user.is_bot:
        user_dto = UserDTO(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

    media_info = []
    if message.photo:
        media_info.append({'type': 'photo', 'file_id': message.photo[-1].file_id})
    if message.document:
        media_info.append({'type': 'document', 'file_id': message.document.file_id})
    if message.audio:
        media_info.append({'type': 'audio', 'file_id': message.audio.file_id})
    if message.video:
        media_info.append({'type': 'video', 'file_id': message.video.file_id})
    if message.voice:
        media_info.append({'type': 'voice', 'file_id': message.voice.file_id})
    if message.sticker:
        media_info.append({'type': 'sticker', 'file_id': message.sticker.file_id})

    forward_from = None
    if message.forward_origin:
        fo = message.forward_origin
        from_id = None
        from_name = None
        if fo.type == 'user':
            from_id = fo.from_user.id
            from_name = fo.from_user.full_name
        elif fo.type == 'chat':
            from_id = fo.from_chat.id
            from_name = fo.from_chat.title
        elif fo.type == 'hidden_user':
            from_name = fo.sender_name
        forward_from = {
            'from_id': from_id,
            'date': message.forward_date.isoformat() if message.forward_date else None,
            'sender_name': from_name
        }

    message_dto = MessageDTO(
        id=message.message_id,
        chat=chat_dto,
        user=user_dto,
        text=message.text or message.caption,
        date=message.date.replace(tzinfo=None),
        edited_date=None,
        reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
        forward_from=forward_from,
        media=media_info if media_info else None
    )

    async for session in get_session():
        repo = MessageRepository(session)
        await repo.save_message(message_dto)
        await session.commit()
        logger.debug(f"Сохранено сообщение {message.message_id} из чата {chat.id}")
        break
