import html
import re
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMINS, OWNER_ID
import database

print("HANDLERS FILE LOADED SUCCESSFULLY")


def get_all_admins_set():
    admins_set = set()
    raw_admins = ADMINS if isinstance(ADMINS, list) else [ADMINS]
    
    for item in raw_admins:
        if isinstance(item, str) and "," in item:
            for sub in item.split(","):
                if sub.strip().isdigit():
                    admins_set.add(int(sub.strip()))
        else:
            try:
                admins_set.add(int(item))
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
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    if user.is_bot:
        return

    all_admins = get_all_admins_set()

    if user.id in all_admins:
        if update.message.reply_to_message:
            await handle_admin_reply(update, context)
        else:
            await update.message.reply_text("ℹ️ عزيزي المشرف، للرد على طالب يرجى استخدام ميزة الرد (Reply) على كارت معلومات الطالب.")
    else:
        await handle_student_message(update, context)


async def handle_student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_admins = get_all_admins_set()
    student_msg_id = update.message.message_id

    try:
        database.save_student(user.id, user.username, user.first_name)
        database.create_ticket(user.id)
    except Exception as db_err:
        print(f"⚠️ DB Error (student_save): {db_err}")

    student_name = html.escape(user.first_name or "طالب")
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"

    text_content = update.message.text or update.message.caption or "[وسائط / ملف / بصمة]"
    msg_text = html.escape(text_content)

    text = (
        "📩 <b>رسالة جديدة من طالب:</b>\n"
        "───────────────────\n"
        f"👤 <b>الاسم:</b> {student_name}\n"
        f"🏷️ <b>المعرف:</b> {student_username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        "───────────────────\n"
        f"💬 <b>الرسالة / الوصف:</b>\n{msg_text}"
    )

    has_media = bool(
        update.message.document or 
        update.message.photo or 
        update.message.voice or 
        update.message.video or 
        update.message.audio or 
        update.message.sticker
    )

    sent_count = 0
    for admin_id in all_admins:
        try:
            sent_info = await context.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
            database.save_message(sent_info.message_id, admin_id, user.id, student_msg_id)

            if has_media:
                copied = await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=user.id,
                    message_id=student_msg_id
                )
                database.save_message(copied.message_id, admin_id, user.id, student_msg_id)

            sent_count += 1
        except Exception as e:
            print(f"❌ فشل إرسال رسالة الطالب للمشرف {admin_id}: {e}")

    if sent_count > 0:
        await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_admins = get_all_admins_set()
    replied_msg = update.message.reply_to_message

    student_id, student_msg_id = database.get_message_info(replied_msg.message_id)

    target_text = replied_msg.text or replied_msg.caption or ""
    if not student_id and target_text:
        match = re.search(r"ID[^\d]*(\d{6,12})", target_text, re.IGNORECASE) or re.search(r"(\d{7,12})", target_text)
        if match:
            student_id = int(match.group(1))

    if not student_id:
        await update.message.reply_text("❌ تعذر تحديد ID الطالب. يرجى التأكد من عمل Reply على كارت معلومات الطالب.")
        return

    # فحص ملكية التذكرة
    try:
        ticket = database.get_ticket(student_id)
        if ticket:
            status, handled_by_id, handled_by_name = ticket
            if handled_by_id and handled_by_id != user.id:
                warning_text = (
                    "⚠️ <b>تنبيه: التذكرة بحوزة مشرف آخر!</b>\n"
                    "───────────────────\n"
                    f"👤 <b>المشرف المسؤول:</b> {handled_by_name}\n\n"
                    "❌ لا يمكنك الرد لأن هذا المشرف متكفل بمتابعة هذا الطالب حالياً."
                )
                await update.message.reply_text(warning_text, parse_mode="HTML", reply_to_message_id=replied_msg.message_id)
                return
    except Exception as e:
        print(f"⚠️ DB Error (get_ticket): {e}")

    admin_username = f"@{user.username}" if user.username else "لا يوجد معرف"
    admin_display_name = f"{html.escape(user.first_name or 'مشرف')} ({admin_username})"

    try:
        # إرسال الرد للطالب مربوطاً برسالته الأصلية
        try:
            if student_msg_id:
                await context.bot.copy_message(
                    chat_id=student_id,
                    from_chat_id=user.id,
                    message_id=update.message.message_id,
                    reply_to_message_id=student_msg_id
                )
            else:
                await context.bot.copy_message(chat_id=student_id, from_chat_id=user.id, message_id=update.message.message_id)
        except Exception:
            await context.bot.copy_message(chat_id=student_id, from_chat_id=user.id, message_id=update.message.message_id)

        database.assign_and_answer_ticket(student_id, user.id, admin_display_name)

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
                # ربط التأكيد والرد بـ Reply مباشر للكارت الأصلي لدى المشرف الذي رد
                reply_id = replied_msg.message_id if admin_id == user.id else None
                
                await context.bot.send_message(chat_id=admin_id, text=notice_text, parse_mode="HTML", reply_to_message_id=reply_id)
                await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"❌ فشل إرسال إشعار الرد للمشرف {admin_id}: {e}")

    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد للطالب: {e}", reply_to_message_id=replied_msg.message_id)


admin_reply = handle_admin_reply
student_message = handle_student_message