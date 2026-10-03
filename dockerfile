FROM python:3.10-slim

# Forzar a Python a mostrar los logs inmediatamente en Render
ENV PYTHONUNBUFFERED=1
# Evitar que Python genere archivos temporales .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias de audio (ffmpeg, libsodium, opus)
# --no-install-recommends evita descargar basura innecesaria para mantener el bot ligero
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsodium-dev \
    libopus0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar SOLO el archivo de requerimientos primero.
# Esto hace que Docker guarde las librerías en caché. Si luego modificas main.py, 
# Render no perderá tiempo volviendo a descargar Discord.py o yt-dlp.
COPY requeriments.txt .

# Instalar las librerías de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requeriments.txt

# Copiar el resto del código del bot
COPY . .

# Comando de inicio
CMD ["python", "main.py"]