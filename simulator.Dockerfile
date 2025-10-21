# Instruksi untuk membangun container simulator

# Gunakan base image Python 3.11 versi slim
FROM python:3.11-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file requirements.txt
COPY requirements.txt .

# Instal semua dependensi Python
# (Meskipun simulator hanya butuh paho-mqtt, lebih mudah menggunakan file yang sama)
RUN pip install -r requirements.txt

# Salin hanya file simulator
COPY robot_simulator.py .

# Perintah default untuk menjalankan simulator
CMD ["python", "robot_simulator.py"]