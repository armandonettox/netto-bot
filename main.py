from telegram.ext import ApplicationBuilder, MessageHandler, filters
from src.bot.handlers import handle_message
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Netto bot rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
