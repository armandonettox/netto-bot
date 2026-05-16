from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.bot.handlers import handle_message, handle_photo, handle_voice, resumo_command
from dotenv import load_dotenv
import logging
import os

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def _log_all(update, context):
    msg = update.message
    if msg:
        logging.info(f"UPDATE recebido — tipo: photo={bool(msg.photo)}, voice={bool(msg.voice)}, text={repr(msg.text)}")


async def _error_handler(update, context):
    logging.error(f"Erro no handler: {context.error}", exc_info=context.error)


def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.ALL, _log_all), group=-1)
    app.add_handler(CommandHandler("resumo", resumo_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(_error_handler)
    print("Netto bot rodando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
