from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from config import TOKEN
import database
import handlers

# إنشاء الجداول
database.create_tables()

print("TOKEN =", repr(TOKEN))

# إنشاء التطبيق
app = Application.builder().token(TOKEN).build()

# أمر /start
app.add_handler(
    CommandHandler(
        "start",
        handlers.start
    )
)

# ردود المشرفين (يجب أن تكون أولًا)
app.add_handler(
    MessageHandler(
        filters.TEXT & filters.REPLY,
        handlers.admin_reply
    ),
    group=0
)

# رسائل الطلاب
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handlers.student_message
    ),
    group=1
)

print("✅ Sixth Bot is running...")

app.run_polling()