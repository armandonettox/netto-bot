from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.bot.handlers import handle_message, resumo_command
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("resumo", resumo_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Netto bot rodando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
