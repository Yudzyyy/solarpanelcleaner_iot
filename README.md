
Proyek full-stack untuk memonitor dan mengontrol sistem pembersih panel surya otomatis berbasis IoT. Proyek ini mencakup antarmuka web real-time, server backend, dan firmware untuk perangkat keras Arduino/ESP8266.

✨ Fitur Utama

Kontrol Real-time: Memulai, menghentikan, dan memantau proses pembersihan secara langsung dari antarmuka web.

Progress Bar Akurat: Visualisasi progress bar yang sinkron dengan pergerakan fisik robot.

Penjadwalan Otomatis: Atur hingga tiga jadwal pembersihan harian yang disimpan secara permanen di database.

Kontrol Pompa Air: Otomatisasi penyemprotan air selama fase pembersihan.

Riwayat Aktivitas: Semua aktivitas (mulai, berhenti, selesai, jadwal) dicatat dan disimpan di database untuk pelacakan.

Arsitektur Berbasis Event: Menggunakan MQTT untuk komunikasi yang andal antara backend dan perangkat IoT.

Siap Dikembangkan: Dibungkus sepenuhnya dalam Docker untuk kemudahan setup dan deployment.

🛠️ Teknologi yang Digunakan

Frontend: React (Vite), Tailwind CSS

Backend: Python (Flask, Flask-SocketIO)

Komunikasi Real-time (Web): WebSocket (via Socket.IO)

Komunikasi Real-time (IoT): MQTT

Database: PostgreSQL

Hardware: ESP8266 / Arduino

Containerization: Docker, Docker Compose

🚀 Cara Menjalankan (Menggunakan Docker)

Ini adalah cara yang direkomendasikan untuk menjalankan seluruh sistem dengan mudah.

Prasyarat

Docker Desktop terinstal dan berjalan.

Langkah-langkah

Clone Repository Ini:

git clone [URL_REPOSITORY_ANDA]
cd [NAMA_FOLDER_PROYEK]


Jalankan Docker Compose:
Buka satu terminal di folder utama proyek dan jalankan perintah berikut. Ini akan membangun dan memulai semua layanan (frontend, backend, database, mosquitto).

docker-compose up --build


Akses Aplikasi:

Buka browser dan akses antarmuka web di: http://localhost:5173

Backend API berjalan di http://localhost:5000.

📂 Struktur Folder Proyek

.
├── arduino_code/
│   └── Solar_Panel_Cleaner.ino     # Kode untuk hardware
├── public/
│   └── solarpanel.jpg              # Aset gambar
├── src/
│   └── SolarPanelCleaner.jsx       # Komponen utama React
├── backend.py                      # Server Flask & SocketIO
├── docker-compose.yml              # Konfigurasi orkestrasi Docker
├── backend.Dockerfile              # Instruksi build Docker untuk backend
├── frontend.Dockerfile             # Instruksi build Docker untuk frontend
├── mosquitto.conf                  # Konfigurasi broker MQTT
├── package.json                    # Dependensi frontend
└── requirements.txt                # Dependensi backend
