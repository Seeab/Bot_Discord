FROM python:3.11-slim

# Instalar ffmpeg y limpiar la caché para que la imagen sea más ligera
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar todos los archivos del repositorio al contenedor
COPY . .

# Instalar las dependencias (usando el nombre exacto de tu archivo)
RUN pip install --no-cache-dir -r requeriments.txt

# Ejecutar el archivo principal del bot
CMD ["python", "main.py"]