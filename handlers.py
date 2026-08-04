import html
import re
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMINS, OWNER_ID
import database

print("HANDLERS FILE LOADED")


def get_all_admins_set():
    admins_set = set()
    for a in ADMINS:
        try:
            admins_set.add(int(a))
        except (ValueError, TypeError):
            pass
    if OWNER_ID:
        try:
            admins_set.add(int(OWNER_ID))
        except (ValueError, TypeError):
            pass
    return admins_set


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 أهلًا بك في مساعد تجي🤍!\n\n"
        "أرسل سؤالك أو استفسارك، وسيتم الرد عليك بأسرع وقت 🤍"
    )


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return

    all_admins = get_all_admins_set()

    if user.id in all_admins:
        if update.message and update.message.reply_to_message:
            await handle_admin_reply(update, context)
        else:
            await update.message.reply_text("ℹ️ عزيزي المشرف، للرد على طالب يرجى استخدام ميزة الرد (Reply) على كارت معلومات الطالب.")
    else:
        await handle_student_message(update, context)


async def handle_student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_admins = get_all_admins_set()

    try:
        database.save_student(user.id, user.username, user.first_name)
        database.create_ticket(user.id)
    except Exception as db_err:
        print(f"⚠️ DB Error (save_student/create_ticket): {db_err}")

    student_name = html.escape(user.first_name or "طالب")
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"

    text_content = update.message.text or update.message.caption
    raw_text = text_content if text_content else "[ملف / وسائط / بصمة صوتية]"
    msg_text = html.escape(raw_text)

    text = (
        "📩 <b>رسالة جديدة من طالب:</b>\n"
        "───────────────────\n"
        f"👤 <b>الاسم:</b> {student_name}\n"
        f"🏷️ <b>المعرف:</b> {student_username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        "───────────────────\n"
        f"💬 <b>الرسالة / الوصف:</b>\n{msg_text}"
    )

    has_attachment = bool(
        update.message.document or 
        update.message.photo or 
        update.message.voice or 
        update.message.video or 
        update.message.audio or 
        update.message.sticker
    )

    sent_success = False
    for admin in all_admins:
        try:
            sent_info = await context.bot.send_message(chat_id=admin, text=text, parse_mode="HTML")
            
            try:
                database.save_message(sent_info.message_id, admin, user.id)
            except Exception as db_err:
                print(f"⚠️ DB Error (save_message): {db_err}")

            if has_attachment or not update.message.text:
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


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_admins = get_all_admins_set()

    replied_msg = update.message.reply_to_message
    student_id = None

    try:
        student_id = database.get_student(replied_msg.message_id)
    except Exception as db_err:
        print(f"⚠️ DB Error (get_student): {db_err}")

    target_text = replied_msg.text or replied_msg.caption or ""
    if not student_id and target_text:
        match = re.search(r"ID[^\d]*(\d{6,12})", target_text, re.IGNORECASE) or re.search(r"(\d{7,12})", target_text)
        if match:
            student_id = int(match.group(1))

    if not student_id:
        await update.message.reply_text("❌ تعذر تحديد ID الطالب. يرجى التأكد من عمل Reply على كارت معلومات الطالب.")
        return

    try:
        ticket = database.get_ticket(student_id)
        if ticket and ticket[0] == "answered":
            handled_by = ticket[1] or "مشرف آخر"
            warning_text = (
                "⚠️ <b>تنبيه: تم الرد على هذه الرسالة مسبقًا!</b>\n"
                "───────────────────\n"
                f"👤 <b>المشرف المسؤول:</b> {handled_by}\n\n"
                "❌ لا يمكنك إرسال رد آخر لهذه التذكرة المغلقة."
            )
            await update.message.reply_text(warning_text, parse_mode="HTML")
            return
    except Exception as e:
        print(f"⚠️ DB Error (get_ticket): {e}")

    admin_username = f"@{user.username}" if user.username else "لا يوجد معرف"
    admin_display_name = f"{html.escape(user.first_name or 'مشرف')} ({admin_username})"

    try:
        database.answer_ticket(student_id, admin_display_name)

        await context.bot.send_message(chat_id=student_id, text="💬 <b>رد من مساعد تجي🤍:</b>", parse_mode="HTML")
        await context.bot.copy_message(
            chat_id=student_id,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )

        notice_text = (
            "✅ <b>تم الرد على الطالب بنجاح!</b>\n"
            "───────────────────\n"
            f"👤 <b>المشرف المسؤول:</b> {html.escape(user.first_name or 'مشرف')}\n"
            f"🏷️ <b>المعرف:</b> {admin_username}\n"
            f"🆔 <b>آيدي الطالب:</b> <code>{student_id}</code>\n"
            "───────────────────\n"
            "👇 <b>محتوى الرد المرسل:</b>"
        )

        for admin_id in all_admins:
            try:
                await context.bot.send_message(chat_id=admin_id, text=notice_text, parse_mode="HTML")
                await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"❌ فشل الإرسال للمشرف {admin_id}: {e}")

    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد للطالب: {e}")