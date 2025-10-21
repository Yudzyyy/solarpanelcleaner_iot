# Instruksi untuk membangun container backend

# Gunakan base image Python 3.11 versi slim
FROM python:3.11-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file requirements.txt
COPY requirements.txt .

# Instal semua dependensi Python
RUN pip install -r requirements.txt

# Salin sisa kode proyek
COPY . .

# Beri tahu Docker bahwa container akan menggunakan port 5000
EXPOSE 5000

# Perintah default untuk menjalankan server backend
CMD ["python", "backend.py"]
