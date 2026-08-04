import html
import re
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

    # تجاهل رسائل المشرفين أنفسهم
    if user.id in ADMINS or user.id == OWNER_ID:
        return

    # حفظ بيانات الطالب وإعادة فتح تذكرة جديدة
    try:
        database.save_student(user.id, user.username, user.first_name)
        database.create_ticket(user.id)
    except Exception as db_err:
        print(f"⚠️ DB Error (save_student): {db_err}")

    student_name = html.escape(user.first_name or "طالب")
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"

    text_content = update.message.text or update.message.caption
    raw_text = text_content if text_content else "[ملف / وسائط / بصمة صوتية]"
    msg_text = html.escape(raw_text)

    text = (
        "📩 <b>رسالة جديدة من طالب:</b>\n"
        f"👤 <b>الاسم:</b> {student_name}\n"
        f"🏷️ <b>المعرف:</b> {student_username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
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
    for admin in ADMINS:
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


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMINS and user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يرجى عمل رد (Reply) على كارت معلومات الطالب الذي يحتوي على الـ ID.")
        return

    replied_msg = update.message.reply_to_message
    student_id = None

    # 1. استخراج الـ ID من قاعدة البيانات
    try:
        student_id = database.get_student(replied_msg.message_id)
    except Exception as db_err:
        print(f"⚠️ DB Error (get_student): {db_err}")

    # 2. استخراج الـ ID من نص الرسالة كبديل
    target_text = replied_msg.text or replied_msg.caption or ""
    if not student_id and target_text:
        match = re.search(r"ID[^\d]*(\d{6,12})", target_text, re.IGNORECASE) or re.search(r"(\d{7,12})", target_text)
        if match:
            student_id = int(match.group(1))

    if not student_id:
        await update.message.reply_text("❌ تعذر تحديد ID الطالب. يرجى التأكد من عمل Reply على (بطاقة معلومات الطالب) التي تحتوي على الاسم والـ ID.")
        return

    # 3. الفحص: هل تمت الإجابة على هذه الرسالة مسبقًا؟
    try:
        ticket = database.get_ticket(student_id)
        if ticket and ticket[0] == "answered":
            handled_by = ticket[1] or "مشرف آخر"
            await update.message.reply_text(f"⚠️ تم الرد على هذه الرسالة مسبقًا بواسطة المشرف {handled_by}.")
            return
    except Exception as e:
        print(f"⚠️ DB Error (get_ticket): {e}")

    admin_identifier = f"@{user.username}" if user.username else user.first_name

    try:
        # إرسال الرد للطالب
        await context.bot.send_message(chat_id=student_id, text="💬 <b>رد من مساعد تجي🤍:</b>", parse_mode="HTML")
        await context.bot.copy_message(
            chat_id=student_id,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )

        # تحديث حالة الرسالة في قاعدة البيانات
        try:
            database.answer_ticket(student_id, admin_identifier)
        except Exception as e:
            print(f"⚠️ DB Error (answer_ticket): {e}")

        await update.message.reply_text("✅ تم إرسال الرد إلى الطالب بنجاح.")

        # 4. إرسال إشعار لبقية المشرفين متضمنًا الرد والمُجيب
        all_admins = set(ADMINS + [OWNER_ID])
        other_admins = [a for a in all_admins if a != user.id]

        notice_text = (
            f"📢 <b>تنويه للمشرفين:</b>\n"
            f"قام المشرف {admin_identifier} بالرد على الطالب (ID: <code>{student_id}</code>).\n\n"
            f"👇 <b>محتوى الرد المرسل:</b>"
        )

        for admin_id in other_admins:
            try:
                await context.bot.send_message(chat_id=admin_id, text=notice_text, parse_mode="HTML")
                await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"❌ فشل إشعار الأدمن {admin_id}: {e}")

    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد للطالب: {e}")