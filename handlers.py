async def student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    # إذا كان المرسل أدمن، يتجاهل البوت الرسالة
    if user.id in ADMINS or user.id == OWNER_ID:
        return

    # حفظ بيانات الطالب مع حماية الكود من التوقف إذا فشلت قاعدة البيانات
    try:
        database.save_student(user.id, user.username, user.first_name)
        database.create_ticket(user.id)
    except Exception as db_err:
        print(f"⚠️ Database error (ignored): {db_err}")

    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"
    msg_text = update.message.text if update.message.text else "[وسائط / بصمة صوتية]"

    text = (
        "📩 **رسالة جديدة من طالب:**\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🏷️ المعرف: {student_username}\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"💬 **الرسالة:**\n{msg_text}"
    )

    sent_success = False
    for admin in ADMINS:
        try:
            sent_info = await context.bot.send_message(chat_id=admin, text=text, parse_mode="Markdown")
            
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
            print(f"❌ فشل الإرسال للأدمن {admin}: {e}")

    if sent_success:
        await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")