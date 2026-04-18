import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import pytesseract
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

def detect_bubbles(img_cv):
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bubbles = []
    h, w = img_cv.shape[:2]

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch
        if area < 1500 or area > (w * h * 0.7):
            continue
        roi = gray[y:y+ch, x:x+cw]
        white_ratio = np.sum(roi > 180) / roi.size
        if white_ratio > 0.45:
            bubbles.append((x, y, cw, ch))

    return merge_overlapping(bubbles)

def merge_overlapping(boxes, overlap_thresh=0.4):
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: b[2]*b[3], reverse=True)
    keep = []
    for box in boxes:
        x1, y1, w1, h1 = box
        dominated = False
        for kx, ky, kw, kh in keep:
            ix = max(x1, kx)
            iy = max(y1, ky)
            ix2 = min(x1+w1, kx+kw)
            iy2 = min(y1+h1, ky+kh)
            if ix2 > ix and iy2 > iy:
                inter = (ix2-ix) * (iy2-iy)
                if inter / (w1*h1) > overlap_thresh:
                    dominated = True
                    break
        if not dominated:
            keep.append(box)
    return keep

def check_tesseract():
    """Cek apakah tesseract terinstall"""
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
        langs = pytesseract.get_languages()
        logger.info(f"Available languages: {langs}")
    except Exception as e:
        logger.error(f"Tesseract NOT found: {e}")

# Cek saat module diload
check_tesseract()

def read_text(img_pil, x, y, w, h):
    padding = 8
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img_pil.width, x + w + padding)
    y2 = min(img_pil.height, y + h + padding)
    cropped = img_pil.crop((x1, y1, x2, y2))

    cropped_cv = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cropped_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed = Image.fromarray(thresh)

    text = ""
    try:
        text = pytesseract.image_to_string(processed, lang='jpn+jpn_vert', config='--psm 6').strip()
    except:
        pass

    if not text or len(text.strip()) < 2:
        try:
            text = pytesseract.image_to_string(processed, lang='eng+ita+por', config='--psm 6').strip()
        except:
            pass

    if not text or len(text.strip()) < 2:
        try:
            text = pytesseract.image_to_string(processed, config='--psm 6').strip()
        except:
            pass

    return text.strip()

def translate_text(text):
    if not text or len(text.strip()) < 2:
        return ""
    try:
        translator = GoogleTranslator(source='auto', target='id')
        return translator.translate(text) or text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def get_font(size=16):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        try:
            bbox = draw.textbbox((0, 0), " ".join(current), font=font)
            tw = bbox[2] - bbox[0]
        except:
            tw = len(" ".join(current)) * 8
        if tw > max_width and len(current) > 1:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

def erase_text(img_cv, x, y, w, h):
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    pad = 8
    x1, y1 = max(0, x+pad), max(0, y+pad)
    x2, y2 = min(img_cv.shape[1], x+w-pad), min(img_cv.shape[0], y+h-pad)
    roi = gray[y1:y2, x1:x2]
    _, text_mask = cv2.threshold(roi, 128, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((3, 3), np.uint8)
    text_mask = cv2.dilate(text_mask, kernel, iterations=2)
    mask[y1:y2, x1:x2] = text_mask
    return cv2.inpaint(img_cv, mask, 7, cv2.INPAINT_TELEA)

def draw_text(img_pil, x, y, w, h, text):
    draw = ImageDraw.Draw(img_pil)
    pad = 10
    max_w = w - pad * 2
    max_h = h - pad * 2
    font_size = 18
    while font_size >= 8:
        font = get_font(font_size)
        lines = wrap_text(text, font, max_w, draw)
        try:
            bbox = draw.textbbox((0, 0), "A", font=font)
            lh = (bbox[3] - bbox[1]) + 3
        except:
            lh = font_size + 3
        if len(lines) * lh <= max_h:
            break
        font_size -= 1

    font = get_font(max(font_size, 8))
    lines = wrap_text(text, font, max_w, draw)
    try:
        bbox = draw.textbbox((0, 0), "A", font=font)
        lh = (bbox[3] - bbox[1]) + 3
    except:
        lh = font_size + 3

    total_h = len(lines) * lh
    start_y = y + (h - total_h) // 2

    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
        except:
            lw = len(line) * font_size * 0.6
        tx = x + (w - lw) // 2
        ty = start_y + i * lh
        draw.text((tx+1, ty+1), line, font=font, fill=(180, 180, 180))
        draw.text((tx, ty), line, font=font, fill=(0, 0, 0))

def process_manga_image(image_bytes):
    try:
        img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        logger.info(f"Image size: {img_pil.size}")

        bubbles = detect_bubbles(img_cv)
        logger.info(f"Detected {len(bubbles)} bubbles")

        if not bubbles:
            return None

        translated_count = 0
        for (x, y, w, h) in bubbles:
            text = read_text(img_pil, x, y, w, h)
            if not text or len(text.strip()) < 2:
                continue
            logger.info(f"OCR: {text[:60]}")
            translated = translate_text(text)
            if not translated or translated.strip() == text.strip():
                continue
            logger.info(f"Translated: {translated[:60]}")
            img_cv = erase_text(img_cv, x, y, w, h)
            img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            draw_text(img_pil, x, y, w, h, translated)
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            translated_count += 1

        logger.info(f"Done: {translated_count} translated")
        if translated_count == 0:
            return None

        output = io.BytesIO()
        img_pil.save(output, format='PNG')
        output.seek(0)
        return output

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
