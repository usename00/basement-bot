FROM python:3.10-slim

# تثبيت opus
RUN apt-get update && apt-get install -y libopus0 ffmpeg

# تحديد مكان المشروع
WORKDIR /app

# نسخ الملفات
COPY . .

# تثبيت الباكدجات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "basement.py"]
