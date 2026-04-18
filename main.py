import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from translator import process_manga_image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎌 *Manga Translator Bot*\n\n"
        "Kirim gambar manga, aku terjemahin ke Bahasa Indonesia!\n\n"
        "📌 *Supported language:*\n"
        "• Jepang 🇯🇵\n"
        "• Inggris 🇬🇧\n"
        "• Italia 🇮🇹\n"
        "• Portugal 🇵🇹\n\n"
        "Tinggal kirim gambarnya aja bang! 🚀",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Cara Pakai:*\n\n"
        "1. Kirim foto/gambar manga\n"
        "2. Tunggu proses terjemahan\n"
        "3. Terima gambar dengan teks Indonesia\n\n"
        "⚠️ *Tips:*\n"
        "• Gambar lebih jelas = hasil lebih akurat\n"
        "• Resolusi tinggi lebih bagus\n"
        "• 1 gambar per pesan",
        parse_mode="Markdown"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Bot aktif dan jalan normal!*\n\n"
        "🤖 Status: Online\n"
        "🌐 Translator: Ready\n"
        "📸 OCR: Ready\n\n"
        "Kirim gambar manga untuk mulai terjemahan!",
        parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(word in text for word in ["halo", "hai", "hello", "hi", "test"]):
        await update.message.reply_text("Halo! Bot aktif nih 👋\nKirim gambar manga buat diterjemah ya!")
    else:
        await update.message.reply_text("Kirim gambar manga aja bang, nanti aku terjemahin ke Indonesia! 🎌")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Lagi proses... tunggu sebentar bang!")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        await msg.edit_text("🔍 Mendeteksi teks di gambar...")
        result_image = await asyncio.to_thread(process_manga_image, bytes(image_bytes))
        if result_image is None:
            await msg.edit_text("❌ Gagal memproses gambar. Coba lagi dengan gambar yang lebih jelas.")
            return
        await msg.edit_text("✅ Selesai! Mengirim hasil...")
        await update.message.reply_photo(
            photo=result_image,
            caption="✅ Terjemahan selesai!"
        )
        await msg.delete()
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}\n\nCoba lagi ya bang!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Kirim gambar aja ya bang, bukan file lain!")
        return
    msg = await update.message.reply_text("⏳ Lagi proses... tunggu sebentar bang!")
    try:
        file = await context.bot.get_file(doc.file_id)
        image_bytes = await file.download_as_bytearray()
        await msg.edit_text("🔍 Mendeteksi teks di gambar...")
        result_image = await asyncio.to_thread(process_manga_image, bytes(image_bytes))
        if result_image is None:
            await msg.edit_text("❌ Gagal memproses gambar. Coba lagi dengan gambar yang lebih jelas.")
            return
        await msg.edit_text("✅ Selesai! Mengirim hasil...")
        await update.message.reply_photo(
            photo=result_image,
            caption="✅ Terjemahan selesai!"
        )
        await msg.delete()
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}\n\nCoba lagi ya bang!")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan! Set environment variable BOT_TOKEN")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
