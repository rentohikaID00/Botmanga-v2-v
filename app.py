import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "Sabar ya, lagi dibaca sama Gemini...")
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Kirim langsung ke Gemini buat deteksi teks & translate
        response = model.generate_content([
            "Ini adalah halaman manga. Cari semua teks bahasa Inggris/Jepang, "
            "lalu berikan daftar terjemahannya saja dalam Bahasa Indonesia.",
            {"mime_type": "image/jpeg", "data": downloaded_file}
        ])
        
        bot.reply_to(message, f"Hasil Terjemahan:\n\n{response.text}")
    except Exception as e:
        bot.reply_to(message, f"Aduh error: {str(e)}")

print("Bot Ringan Jalan...")
bot.infinity_polling()
