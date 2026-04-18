FROM python:3.10-slim

# Install library sistem yang lebih umum/standar
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install requirements tanpa simpan cache
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
