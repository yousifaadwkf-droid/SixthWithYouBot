import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
# استيراد الإعدادات من ملف config.py
import config

# إعداد الـ Logging لمتابعة الأخطاء في Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in config.ADMINS or user_id == config.OWNER_ID:
        await update.message.reply_text("أهلاً بك يا أدمن! البوت جاهز لاستقبال رسائل الطلاب والرد عليها.")
    else:
        await update.message.reply_text("أهلاً بك! يمكنك إرسال استفسارك هنا (نص، صوت، صورة، فيديو، أو ملف) وسيرد عليك المشرف في أقرب وقت.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. إذا كانت الرسالة قادمة من طالب -> توجيهها للمشرفين
    if user_id not in config.ADMINS and user_id != config.OWNER_ID:
        try:
            # توجيه الرسالة كما هي إلى المشرف الأساسي
            await update.message.forward(chat_id=config.OWNER_ID)
            await update.message.reply_text("تم إرسال رسالتك إلى المشرفين بنجاح.")
        except Exception as e:
            logging.error(f"Error forwarding message: {e}")
            await update.message.reply_text("حدث خطأ أثناء إرسال رسالتك، يرجى المحاولة لاحقاً.")
            
    # 2. إذا كانت الرسالة قادمة من المشرف رداً على رسالة طالب -> إرسال الرد للطالب
    else:
        if update.message.reply_to_message:
            original_message = update.message.reply_to_message
            if original_message.forward_from:
                target_user_id = original_message.forward_from.id
                try:
                    # نسخ الرسالة وإرسالها للطالب (تنسخ الصوت، الصورة، النص... إلخ)
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
    # التأكد من وجود التوكن
    if not config.TOKEN:
        print("❌ Error: TOKEN is missing! Check your Environment Variables.")
        return

    # إنشاء التطبيق
    app = Application.builder().token(config.TOKEN).build()

    # إضافة الأوامر والمُعالج لجميع الوسائط والنصوص
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(~filters.COMMAND & filters.ALL, handle_message))

    print(f"✅ {config.BOT_NAME} is running successfully...")
    
    # تشغيل البوت مع تجاهل التحديثات المتراكمة القديمة
    app.run_polling(drop_pending_updates=True)

# الشرط المزدوج الصحيح لتشغيل الملف
if name == "__main__":
    main()