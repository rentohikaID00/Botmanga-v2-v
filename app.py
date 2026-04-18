import os
import easyocr
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Ambil API KEY dari file .env
load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up Gemini
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Versi cepat dan irit limit

def translate_teks(teks, asal):
    prompt = f"Terjemahkan teks manga ini dari bahasa {asal} ke Bahasa Indonesia yang santai/gaul. Hasilnya cukup teks translasinya saja: {teks}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return teks # Jika gagal translate, balikkan teks asli

def eksekusi_bot(input_img, output_img):
    # 1. Baca Gambar (Deteksi teks Inggris & Jepang)
    reader = easyocr.Reader(['en', 'ja'])
    results = reader.readtext(input_img)

    img = Image.open(input_img).convert("RGB")
    draw = ImageDraw.Draw(img)

    for (bbox, text, prob) in results:
        if prob < 0.3: continue # Abaikan kalau teks gak jelas

        # Ambil posisi kotak teks
        x_min = min([p[0] for p in bbox])
        y_min = min([p[1] for p in bbox])
        x_max = max([p[0] for p in bbox])
        y_max = max([p[1] for p in bbox])

        # 2. Translate
        bahasa_asal = "Jepang" if any(ord(c) > 127 for c in text) else "Inggris"
        hasil_indo = translate_teks(text, bahasa_asal)
        print(f"Ori: {text} -> Indo: {hasil_indo}")

        # 3. Hapus Teks Lama (Timpa Putih)
        draw.rectangle([x_min, y_min, x_max, y_max], fill="white")

        # 4. Tempel Teks Baru
        try:
            # Gunakan font bawaan jika file .ttf tidak ada
            font = ImageFont.load_default() 
            draw.text((x_min, y_min), hasil_indo, fill="black", font=font)
        except:
            draw.text((x_min, y_min), hasil_indo, fill="black")

    img.save(output_img)
    print(f"Selesai! Cek file: {output_img}")

if __name__ == "__main__":
    # Ganti 'manga.jpg' dengan nama file yang ingin kamu tes
    eksekusi_bot("input.jpg", "hasil_output.jpg")
