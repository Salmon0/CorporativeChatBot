import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from config import settings
from .handlers import (
    start, help_command, export, status, chats_command,
    handle_incoming_message, handle_chat_selection
)
from .filters import AdminFilter

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def create_bot() -> Application:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    admin_filter = AdminFilter()

    # Команды администраторов
    application.add_handler(CommandHandler("start", start, filters=admin_filter))
    application.add_handler(CommandHandler("help", help_command, filters=admin_filter))
    application.add_handler(CommandHandler("chats", chats_command, filters=admin_filter))
    application.add_handler(CommandHandler("export", export, filters=admin_filter))
    application.add_handler(CommandHandler("status", status, filters=admin_filter))

    # Обработчик нажатий на инлайн-кнопки
    application.add_handler(CallbackQueryHandler(handle_chat_selection))

    # Обработчик всех входящих сообщений (не команд) для сохранения
    application.add_handler(MessageHandler(
        filters.UpdateType.MESSAGES & ~filters.COMMAND,
        handle_incoming_message
    ))

    application.add_error_handler(error_handler)

    return application

async def run_bot():
    app = create_bot()
    logger.info("Бот запущен и ожидает команды...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки бота")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()