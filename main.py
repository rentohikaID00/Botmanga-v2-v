import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from translator import process_manga_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Translate Manga\n\n"
        "Kirim gambar manga, nanti gue terjemahin ke Indonesia 👍"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Lagi proses...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        input_path = "input.jpg"
        output_path = "output.jpg"

        await file.download_to_drive(input_path)

        result = process_manga_image(input_path, output_path)

        if not result:
            await msg.edit_text("❌ Gagal proses gambar")
            return

        await update.message.reply_photo(photo=open(output_path, 'rb'))
        await msg.delete()

    except Exception as e:
        logger.error(e)
        await msg.edit_text(f"❌ Error: {str(e)}")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN belum diset")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app
