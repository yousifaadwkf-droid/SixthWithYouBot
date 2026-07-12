# handlers.py
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMINS, OWNER_ID
import database

print("HANDLERS FILE LOADED")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 أهلًا بك في سادسي!\n\n"
        "أرسل سؤالك أو استفسارك، وسيتم الرد عليك بأسرع وقت 🤍"
    )


async def student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in ADMINS:
        return

    database.save_student(user.id, user.username, user.first_name)
    database.create_ticket(user.id)

    text = (
        "📩 رسالة طالب جديدة\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 الرسالة:\n{update.message.text}"
    )

    for admin in ADMINS:
        sent = await context.bot.send_message(chat_id=admin, text=text)
        database.save_message(sent.message_id, admin, user.id)

    await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMINS:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة الطالب.")
        return

    message_id = update.message.reply_to_message.message_id
    student_id = database.get_student(message_id)

    if student_id is None:
        await update.message.reply_text("❌ لم أجد بيانات هذه الرسالة.")
        return

    status = database.ticket_status(student_id)
    if status is None:
        await update.message.reply_text("❌ لم أجد بيانات السؤال.")
        return

    answered, answered_by = status

    if answered:
        await update.message.reply_text(
            f"⚠️ تمت الإجابة على هذا السؤال بواسطة {answered_by}"
        )
        return

    admin_name = f"@{user.username}" if user.username else user.first_name

    await context.bot.send_message(
        chat_id=student_id,
        text=f"💬 رد من فريق سادسي\n\n{update.message.text}"
    )

    database.answer_ticket(student_id, admin_name)

    for admin_message_id, admin_id in database.get_admin_messages(student_id):
        if admin_id != user.id:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"✅ تمت الإجابة بواسطة {admin_name}",
                    reply_to_message_id=admin_message_id
                )
            except Exception:
                pass

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                "📋 تم الرد على الطالب\n\n"
                f"👨‍💼 المشرف: {admin_name}\n\n"
                f"💬 الرد:\n{update.message.text}"
            )
        )
    except Exception:
        pass

    await update.message.reply_text("✅ تم إرسال الرد للطالب.")
