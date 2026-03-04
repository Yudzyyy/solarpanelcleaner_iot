# ☀️ Solar Panel Cleaner IoT

[![CI/CD Pipeline](https://github.com/Yudzyyy/solarpanelcleaner_iot/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Yudzyyy/solarpanelcleaner_iot/actions/workflows/ci-cd.yml)
[![Docker Backend](https://img.shields.io/docker/v/your-dockerhub-username/solar-cleaner-backend?label=backend&logo=docker)](https://hub.docker.com/r/your-dockerhub-username/solar-cleaner-backend)
[![Docker Frontend](https://img.shields.io/docker/v/your-dockerhub-username/solar-cleaner-frontend?label=frontend&logo=docker)](https://hub.docker.com/r/your-dockerhub-username/solar-cleaner-frontend)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Proyek **full-stack IoT** untuk memonitor dan mengontrol sistem pembersih panel surya otomatis.  
Mencakup **antarmuka web real-time**, **server backend**, dan **firmware** untuk perangkat keras **Arduino/ESP8266**.

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                     │
│                                                                 │
│  ┌──────────────┐     WebSocket      ┌──────────────────────┐  │
│  │   Frontend   │ ◄────────────────► │      Backend         │  │
│  │ React + Vite │    REST API /       │   Python + Flask     │  │
│  │  Port: 5173  │    Socket.IO        │   Port: 5000         │  │
│  └──────────────┘                    └──────┬───────────────┘  │
│                                             │ MQTT Subscribe   │
│                                             ▼                  │
│  ┌──────────────────────┐      ┌────────────────────────────┐  │
│  │   PostgreSQL DB      │      │   Mosquitto MQTT Broker    │  │
│  │   Port: 5433         │      │   Port: 1883 / 9001        │  │
│  └──────────────────────┘      └────────────┬───────────────┘  │
│                                             │ MQTT Publish     │
└─────────────────────────────────────────────┼─────────────────-┘
                                              │
                                    ┌─────────▼──────────┐
                                    │  Hardware (IoT)     │
                                    │  ESP8266 / Arduino  │
                                    └─────────────────────┘
```

---

## 🔄 CI/CD Pipeline

Setiap `git push` ke branch `main` atau `develop` akan memicu pipeline otomatis:

```
Push to GitHub
      │
      ▼
┌─────────────────────────────────────────────┐
│  Job 1: Test & Lint Backend (Python)        │
│  • flake8 linting (syntax & code quality)   │
│  • pytest unit tests                        │
└─────────────────────┬───────────────────────┘
                      │ parallel
┌─────────────────────▼───────────────────────┐
│  Job 2: Test & Lint Frontend (React)        │
│  • ESLint code quality check                │
│  • Vite production build                    │
└─────────────────────┬───────────────────────┘
                      │ (hanya jika push ke main)
┌─────────────────────▼───────────────────────┐
│  Job 3: Build & Push Docker Images          │
│  • Build backend image                      │
│  • Build frontend image                     │
│  • Push ke Docker Hub dengan tag :latest    │
│    dan :sha-xxxxxxx                         │
└─────────────────────────────────────────────┘
```

---

## ✨ Fitur Utama

- **Kontrol Real-time** — Memulai, menghentikan, dan memantau proses pembersihan langsung dari antarmuka web.
- **Progress Bar Akurat** — Visualisasi progress bar yang sinkron dengan pergerakan fisik robot.
- **Penjadwalan Otomatis** — Atur hingga tiga jadwal pembersihan harian yang disimpan di database.
- **Kontrol Pompa Air** — Otomatisasi penyemprotan air selama fase pembersihan.
- **Riwayat Aktivitas** — Semua aktivitas (mulai, berhenti, selesai, jadwal) dicatat dan disimpan.
- **Arsitektur Berbasis Event** — Menggunakan **MQTT** untuk komunikasi yang andal antara backend dan perangkat IoT.
- **CI/CD Otomatis** — GitHub Actions pipeline untuk testing, linting, dan push Docker image otomatis.

---

## 🛠️ Teknologi yang Digunakan

| Komponen             | Teknologi                           |
| -------------------- | ----------------------------------- |
| **Frontend**         | React 19 (Vite), Tailwind CSS       |
| **Backend**          | Python 3.11 (Flask, Flask-SocketIO) |
| **Web Realtime**     | WebSocket (via Socket.IO)           |
| **IoT Realtime**     | MQTT (Mosquitto Broker)             |
| **Database**         | PostgreSQL                          |
| **Hardware**         | ESP8266 / Arduino                   |
| **Containerization** | Docker, Docker Compose              |
| **CI/CD**            | GitHub Actions                      |
| **Registry**         | Docker Hub                          |

---

## 🚀 Cara Menjalankan (Development)

### 🧩 Prasyarat

- **Docker Desktop** telah terinstal dan berjalan.
- **Git** untuk clone repository.

### ⚙️ Langkah-langkah

1. **Clone repository ini**

   ```bash
   git clone https://github.com/Yudzyyy/solarpanelcleaner_iot.git
   cd solarpanelcleaner_iot
   ```

2. **Siapkan environment variables**

   ```bash
   cp .env.example .env
   # Edit file .env dan sesuaikan nilainya
   ```

3. **Jalankan semua service dengan Docker Compose**

   ```bash
   docker compose up --build
   ```

4. **Akses aplikasi**
   - 🌐 Frontend: [http://localhost:5173](http://localhost:5173)
   - 🔌 Backend API: [http://localhost:5000](http://localhost:5000)
   - 🗄️ Database: `localhost:5433`
   - 📡 MQTT Broker: `localhost:1883`

---

## 🧪 Menjalankan Tests Secara Lokal

```bash
# Install dependencies testing
pip install pytest flake8

# Jalankan unit tests
pytest test_backend.py -v

# Jalankan linter Python
flake8 backend.py --max-line-length=127

# Jalankan linter frontend
npm run lint

# Build frontend untuk produksi
npm run build
```

---

## 🔐 Setup GitHub Actions Secrets

Untuk mengaktifkan pipeline CI/CD (push ke Docker Hub), tambahkan secrets berikut di **GitHub → Settings → Secrets and variables → Actions**:

| Secret                | Deskripsi                                 |
| --------------------- | ----------------------------------------- |
| `DOCKER_HUB_USERNAME` | Username Docker Hub kamu                  |
| `DOCKER_HUB_TOKEN`    | Access Token Docker Hub (bukan password!) |

> 💡 **Cara membuat Docker Hub Token**: Login ke [hub.docker.com](https://hub.docker.com) → Account Settings → Security → New Access Token

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

| Komponen             | Teknologi                      |
| -------------------- | ------------------------------ |
| **Frontend**         | React (Vite), Tailwind CSS     |
| **Backend**          | Python (Flask, Flask-SocketIO) |
| **Web Realtime**     | WebSocket (via Socket.IO)      |
| **IoT Realtime**     | MQTT                           |
| **Database**         | PostgreSQL                     |
| **Hardware**         | ESP8266 / Arduino              |
| **Containerization** | Docker, Docker Compose         |

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
   ```
