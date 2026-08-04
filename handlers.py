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

    msg_text = update.message.text if update.message.text else "[وسائط/ملف]"
    text = (
        "📩 **رسالة طالب جديدة**\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🏷️ المعرف: {student_username}\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"💬 **الرسالة:**\n{msg_text}"
    )

    for admin in ADMINS:
        try:
            sent = await context.bot.send_message(chat_id=admin, text=text, parse_mode="Markdown")
            database.save_message(sent.message_id, admin, user.id)
        except Exception as e:
            print(f"Failed to send to admin {admin}: {e}")

    await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMINS and user.id != OWNER_ID:
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
    reply_content = update.message.text if update.message.text else "تم إرسال رد."
    
    await context.bot.send_message(
        chat_id=student_id,
        text=f"💬 **رد من مساعد تجي🤍**\n\n{reply_content}"
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
                "📋 **تم الرد على الطالب**\n\n"
                f"👨‍💼 المشرف: {admin_name}\n\n"
                f"💬 الرد:\n{reply_content}"
            )
        )
    except Exception:
        pass

    await update.message.reply_text("✅ تم إرسال الرد للطالب.")