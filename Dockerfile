FROM python:3.12-slim

# Install Tesseract OCR + Japanese language
RUN apt-get update && apt-get install -y     tesseract-ocr     tesseract-ocr-jpn     tesseract-ocr-eng     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "main.py"]
