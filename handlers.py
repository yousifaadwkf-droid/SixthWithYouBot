import html
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
    if not user:
        return

    # تجاهل الرسائل القادمة من المشرفين أنفسهم
    if user.id in ADMINS or user.id == OWNER_ID:
        return

    # حفظ بيانات الطالب
    try:
        database.save_student(user.id, user.username, user.first_name)
        database.create_ticket(user.id)
    except Exception as db_err:
        print(f"⚠️ Database error: {db_err}")

    # حماية النص من أخطاء التنسيق باستخدام HTML
    student_name = html.escape(user.first_name or "طالب")
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"
    raw_text = update.message.text if update.message.text else "[وسائط / بصمة صوتية]"
    msg_text = html.escape(raw_text)

    text = (
        "📩 <b>رسالة جديدة من طالب:</b>\n"
        f"👤 <b>الاسم:</b> {student_name}\n"
        f"🏷️ <b>المعرف:</b> {student_username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"💬 <b>الرسالة:</b>\n{msg_text}"
    )

    sent_success = False
    for admin in ADMINS:
        try:
            sent_info = await context.bot.send_message(chat_id=admin, text=text, parse_mode="HTML")
            try:
                database.save_message(sent_info.message_id, admin, user.id)
            except Exception:
                pass

            # إرسال نسخة من الوسائط أو البصمة الصوتية إن وجدت
            if not update.message.text:
                sent_copy = await context.bot.copy_message(
                    chat_id=admin,
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
                try:
                    database.save_message(sent_copy.message_id, admin, user.id)
                except Exception:
                    pass

            sent_success = True
        except Exception as e:
            print(f"❌ Error sending to admin {admin}: {e}")

    if sent_success:
        await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMINS and user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id
    student_id = database.get_student(replied_msg_id)

    if not student_id:
        await update.message.reply_text("❌ تعذر العثور على بيانات هذا الطالب.")
        return

    try:
        await context.bot.send_message(chat_id=student_id, text="💬 <b>رد من مساعد تجي🤍:</b>", parse_mode="HTML")
        await context.bot.copy_message(
            chat_id=student_id,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )

        admin_name = f"@{user.username}" if user.username else user.first_name
        database.answer_ticket(student_id, admin_name)

        await update.message.reply_text("✅ تم إرسال الرد إلى الطالب بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد للطالب: {e}")