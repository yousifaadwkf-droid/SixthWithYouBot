import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TOKEN
import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # تسجيل الأوامر والرسائل عبر الموجه الرئيسي
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(~filters.COMMAND, handlers.route_message))

    print("🤖 مساعد تجي🤍 يعمل بنجاح...")
    app.run_polling()


if __name__ == "__main__":
    main()