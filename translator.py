import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator

def process_manga_image(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        return False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    data = pytesseract.image_to_data(thresh, lang='jpn', output_type=Output.DICT)

    pil_img = Image.fromarray(img)
    draw
