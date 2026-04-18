def main():
    print("🚀 BOT STARTING...")

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN KOSONG!")
        raise ValueError("BOT_TOKEN belum diset")

    print("✅ TOKEN ADA")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 BOT JALAN")
    app.run_polling(drop_pending_updates=True)
