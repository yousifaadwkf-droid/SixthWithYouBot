import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# إعداد الـ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8389405270:AAGSAvd7eBulhUrehpxmkCdT9iVzePTGQHs"
OWNER_ID = 5698308826

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        await update.message.reply_text("أهلاً بك يا أدمن! البوت جاهز لاستقبال ورسائل الطلاب والرد عليها.")
    else:
        await update.message.reply_text("أهلاً بك! يمكنك إرسال استفسارك هنا (نص، صوت، صورة، فيديو، أو ملف) وسيرد عليك المشرف في أقرب وقت.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # رسالة من الطالب -> توجيهها للمشرف
    if user_id != OWNER_ID:
        try:
            await update.message.forward(chat_id=OWNER_ID)
            await update.message.reply_text("تم إرسال رسالتك إلى المشرفين بنجاح.")
        except Exception as e:
            logging.error(f"Error forwarding message: {e}")
            await update.message.reply_text("حدث خطأ أثناء إرسال رسالتك، يرجى المحاولة لاحقاً.")
            
    # رد من المشرف -> إرساله للطالب
    else:
        if update.message.reply_to_message:
            original_message = update.message.reply_to_message
            if original_message.forward_from:
                target_user_id = original_message.forward_from.id
                try:
                    await update.message.copy(chat_id=target_user_id)
                    await update.message.reply_text("تم إرسال الرد إلى الطالب بنجاح.")
                except Exception as e:
                    logging.error(f"Error sending reply: {e}")
                    await update.message.reply_text("تعذر إرسال الرد. قد يكون الطالب قد قام بحظر البوت.")
            else:
                await update.message.reply_text("لا يمكن معرفة صاحب الرسالة الأصلي (خاصية التوجيه مغلقة لدى الطالب).")
        else:
            await update.message.reply_text("يرجى استخدام ميزة الـ Reply (الرد) على رسالة الطالب لتتمكن من إجابته.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    
    # يشمل الرسائل النصية وكافة أنواع الوسائط (صوت، صورة، فيديو، ملفات)
    app.add_handler(MessageHandler(~filters.COMMAND & filters.ALL, handle_message))

    print("Bot is running...")
    app.run_polling()

if name == "__main__":
    main()