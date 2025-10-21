# ☀️ Solar Panel Cleaner

Proyek **full-stack IoT** untuk memonitor dan mengontrol sistem pembersih panel surya otomatis.  
Mencakup **antarmuka web real-time**, **server backend**, dan **firmware** untuk perangkat keras **Arduino/ESP8266**.

---

## ✨ Fitur Utama

- **Kontrol Real-time** — Memulai, menghentikan, dan memantau proses pembersihan langsung dari antarmuka web.
- **Progress Bar Akurat** — Visualisasi progress bar yang sinkron dengan pergerakan fisik robot.
- **Penjadwalan Otomatis** — Atur hingga tiga jadwal pembersihan harian yang disimpan di database.
- **Kontrol Pompa Air** — Otomatisasi penyemprotan air selama fase pembersihan.
- **Riwayat Aktivitas** — Semua aktivitas (mulai, berhenti, selesai, jadwal) dicatat dan disimpan.
- **Arsitektur Berbasis Event** — Menggunakan **MQTT** untuk komunikasi yang andal antara backend dan perangkat IoT.
- **Siap Dikembangkan** — Dikemas sepenuhnya dalam **Docker** untuk kemudahan setup dan deployment.

---

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi |
|-----------|------------|
| **Frontend** | React (Vite), Tailwind CSS |
| **Backend** | Python (Flask, Flask-SocketIO) |
| **Web Realtime** | WebSocket (via Socket.IO) |
| **IoT Realtime** | MQTT |
| **Database** | PostgreSQL |
| **Hardware** | ESP8266 / Arduino |
| **Containerization** | Docker, Docker Compose |

---

## 🚀 Cara Menjalankan (Menggunakan Docker)

Cara yang direkomendasikan untuk menjalankan seluruh sistem dengan mudah.

### 🧩 Prasyarat
- **Docker Desktop** telah terinstal dan berjalan.

### ⚙️ Langkah-langkah

1. **Clone repository ini**
   ```bash
   git clone https://github.com/username/solar-panel-cleaner.git
   cd solar-panel-cleaner


