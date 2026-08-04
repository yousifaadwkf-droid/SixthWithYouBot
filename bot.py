import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in config.ADMINS or user_id == config.OWNER_ID:
        await update.message.reply_text("أهلاً بك يا أدمن! البوت جاهز لاستقبال رسائل الطلاب والرد عليها.")
    else:
        await update.message.reply_text("أهلاً بك! يمكنك إرسال استفسارك هنا وسيرد عليك المشرف في أقرب وقت.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # 1. رسالة قادمة من طالب -> إرسالها إلى المشرف
    if user_id not in config.ADMINS and user_id != config.OWNER_ID:
        try:
            # إرسال تفاصيل الطالب أولاً للمشرف
            header_text = f"📩 **رسالة جديدة من طالب:**\n👤 الاسم: {user.full_name}\n🆔 الـ ID: `{user_id}`"
            await context.bot.send_message(
                chat_id=config.OWNER_ID,
                text=header_text,
                parse_mode="Markdown"
            )
            
            # نسخ رسالة الطالب وإرسالها للمشرف
            await update.message.copy(chat_id=config.OWNER_ID)
            await update.message.reply_text("تم إرسال رسالتك إلى المشرفين بنجاح.")
            
        except Exception as e:
            logging.error(f"Error sending message to owner: {e}")
            await update.message.reply_text("حدث خطأ أثناء إرسال رسالتك، يرجى المحاولة لاحقاً.")
            
    # 2. رسالة قادمة من المشرف رداً على الطالب
    else:
        if update.message.reply_to_message:
            # محاولة قراءة ID الطالب من الرسالة المقتبسة
            reply_msg = update.message.reply_to_message
            target_user_id = None
            
            if reply_msg.forward_from:
                target_user_id = reply_msg.forward_from.id
            
            if target_user_id:
                try:
                    await update.message.copy(chat_id=target_user_id)
                    await update.message.reply_text("تم إرسال الرد إلى الطالب بنجاح.")
                except Exception as e:
                    await update.message.reply_text(f"تعذر إرسال الرد: {e}")
            else:
                await update.message.reply_text("للرد على هذا الطالب استخدم الأمر التالية:\n`/reply ID_الطالب الرسالة`", parse_mode="Markdown")
        else:
            await update.message.reply_text("يرجى الرد على الرسالة الموجهة أو استخدام الأمر /reply ID الرسالة.")

# أمر مباشر للمشرف للرد بحسب الـ ID
async def manual_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in config.ADMINS or user_id == config.OWNER_ID:
        if len(context.args) < 2:
            await update.message.reply_text("طريقة الاستخدام:\n`/reply ID_الطالب نص_الرد`", parse_mode="Markdown")
            return
        
        target_id = context.args[0]
        reply_text = " ".join(context.args[1:])
        
        try:
            await context.bot.send_message(chat_id=target_id, text=f"💬 **رد المشرف:**\n\n{reply_text}", parse_mode="Markdown")
            await update.message.reply_text("تم إرسال الرد بنجاح!")
        except Exception as e:
            await update.message.reply_text(f"فشل إرسال الرد: {e}")

def main():
    if not config.TOKEN:
        print("❌ Error: TOKEN is missing!")
        return

    app = Application.builder().token(config.TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", manual_reply))
    app.add_handler(MessageHandler(~filters.COMMAND & filters.ALL, handle_message))

    print(f"✅ {config.BOT_NAME} is running successfully...")
    app.run_polling(drop_pending_updates=True)

if name == "__main__":
    main()