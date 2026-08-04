from telegram import Update
from telegram.ext import ContextTypes
from config import ADMINS, OWNER_ID
import database

print("HANDLERS FILE LOADED")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 أهلًا بك في مساعد تجي🤍!\n\n"
        "أرسل سؤالك أو استفسارك، وسيتم الرد عليك بأسرع وقت 🤍"
    )


async def student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in ADMINS or user.id == OWNER_ID:
        return

    # حفظ بيانات الطالب
    database.save_student(user.id, user.username, user.first_name)
    database.create_ticket(user.id)

    # تجهيز المعرف بشكل آمن
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"
    msg_text = update.message.text if update.message.text else "[وسائط / بصمة صوتية]"

    text = (
        "📩 **رسالة جديدة من طالب:**\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🏷️ المعرف: {student_username}\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"💬 **الرسالة:**\n{msg_text}"
    )

    for admin in ADMINS:
        try:
            # إرسال تفاصيل الطالب إلى المشرف
            sent_info = await context.bot.send_message(chat_id=admin, text=text, parse_mode="Markdown")
            database.save_message(sent_info.message_id, admin, user.id)

            # إذا كانت رسالة الطالب بصمة صوتية أو صورة، يتم نسخها وإرسالها للمشرف أيضاً
            if not update.message.text:
                sent_copy = await context.bot.copy_message(
                    chat_id=admin,
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
                database.save_message(sent_copy.message_id, admin, user.id)

        except Exception as e:
            print(f"Failed to send to admin {admin}: {e}")

    await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMINS and user.id != OWNER_ID:
        return

    # التأكد من أن المشرف قام بعمل Reply على رسالة الطالب
    if not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id
    student_id = database.get_student(replied_msg_id)

    if not student_id:
        await update.message.reply_text("❌ تعذر العثور على بيانات هذا الطالب.")
        return

    try:
        # إرسال إشعار للطالب ثم نسخ الرد (سواء كان نصًا أو بصمة صوتية أو ملفًا)
        await context.bot.send_message(chat_id=student_id, text="💬 **رد من مساعد تجي🤍:**", parse_mode="Markdown")
        await context.bot.copy_message(
            chat_id=student_id,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )

        admin_name = f"@{user.username}" if user.username else user.first_name
        database.answer_ticket(student_id, admin_name)

        await update.message.reply_text("✅ تم إرسال الرد/البصمة الصوتية إلى الطالب بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد للطالب: {e}")