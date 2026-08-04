import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import config
import handlers

# إعداد السجلات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def main():
    if not config.TOKEN:
        print("❌ Error: TOKEN is missing!")
        return

    app = Application.builder().token(config.TOKEN).build()

    # ربط المعالجات الجديدة من ملف handlers.py
    app.add_handler(CommandHandler("start", handlers.start))
    
    # الرد التلقائي من أدمن عبر عمل Reply على الرسالة (بما فيها الصوت والوسائط)
    app.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handlers.admin_reply))
    
    # استقبال رسائل الطلاب (نصوص، صور، بصمات صوتية)
    app.add_handler(MessageHandler(~filters.COMMAND & filters.ALL, handlers.student_message))

    print(f"✅ {config.BOT_NAME} is running successfully...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()