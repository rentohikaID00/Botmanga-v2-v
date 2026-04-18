import os
import logging
import easyocr
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load kunci-kunci rahasia
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Inisialisasi OCR (Beban berat, jadi kita load di awal sekali saja)
print("Sedang memuat model OCR (Jepang & Inggris)...")
reader = easyocr.Reader(['en', 'ja'])

# Fungsi Translate via Gemini
def translate_teks(teks, asal):
    prompt = f"Terjemahkan teks manga ini dari bahasa {asal} ke Bahasa Indonesia yang santai. Cukup hasil translasinya saja: {teks}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return teks

# Fungsi Proses Gambar
async def process_image(input_path, output_path):
    img = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    results = reader.readtext(input_path)

    for (bbox, text, prob) in results:
        if prob < 0.3: continue
        
        x_min, y_min = map(int, bbox[0])
        x_max, y_max = map(int, bbox[2])

        # Translate
        bahasa_asal = "Jepang" if any(ord(c) > 127 for c in text) else "Inggris"
        hasil_indo = translate_teks(text, bahasa_asal)

        # Timpa kotak putih & tulis teks
        draw.rectangle([x_min, y_min, x_max, y_max], fill="white")
        draw.text((x_min, y_min), hasil_indo, fill="black")

    img.save(output_path)

# Handler saat user kirim foto
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gambar diterima! Sedang diproses, tunggu bentar ya...")
    
    # Download foto
    photo_file = await update.message.photo[-1].get_file()
    input_p = "input.jpg"
    output_p = "hasil.jpg"
    await photo_file.download_to_drive(input_p)

    # Proses
    try:
        await process_image(input_p, output_p)
        # Kirim balik
        await update.message.reply_photo(photo=open(output_p, 'rb'), caption="Ini hasilnya bos!")
    except Exception as e:
        await update.message.reply_text(f"Waduh error: {e}")

# Main program
if __name__ == '__main__':
    print("Bot Telegram Jalan...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
