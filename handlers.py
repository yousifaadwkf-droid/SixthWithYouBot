async def student_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in ADMINS or user.id == OWNER_ID:
        return

    # حفظ بيانات الطالب والتذكرة
    database.save_student(user.id, user.username, user.first_name)
    database.create_ticket(user.id)

    # تجهيز يوزر الطالب (المعرف)
    student_username = f"@{user.username}" if user.username else "لا يوجد معرف"

    msg_text = update.message.text if update.message.text else "[وسائط/ملف]"
    text = (
        "📩 رسالة طالب جديدة\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🏷️ المعرف: {student_username}\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"💬 الرسالة:\n{msg_text}"
    )

    for admin in ADMINS:
        try:
            sent = await context.bot.send_message(chat_id=admin, text=text, parse_mode="Markdown")
            database.save_message(sent.message_id, admin, user.id)
        except Exception as e:
            print(f"Failed to send to admin {admin}: {e}")

    await update.message.reply_text("✅ تم استلام رسالتك وسيتم الرد عليك قريبًا.")
