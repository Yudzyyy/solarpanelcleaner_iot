# File: robot_simulator.py (Versi Perbaikan dengan Threading)

import paho.mqtt.client as mqtt
import time
import threading

# --- Konfigurasi ---
MQTT_BROKER = "172.29.192.1" # Pastikan IP ini sudah benar
MQTT_PORT = 1883
CLIENT_ID = "RobotSimulator"
TOPIC_COMMAND = "robot/command"
TOPIC_STATUS = "robot/status"

# Event untuk menghentikan thread yang sedang berjalan
stop_process_event = threading.Event()

# --- Fungsi yang berjalan di Thread terpisah ---

def process_start(client):
    """Jalankan ini di thread saat 'start' diterima"""
    print("   ⬇️  Memulai gerakan TURUN... (akan memakan waktu 2 menit)")
    
    # time.sleep(120) diganti dengan event.wait(120)
    # Ini akan menunggu 120 detik, TAPI bisa diinterupsi oleh event.set()
    interrupted = stop_process_event.wait(timeout=3) ##BAGIAN SERING DIGANTI
    
    if interrupted:
        # Jika diinterupsi (karena 'return' ditekan)
        print("   ⏹️  Proses TURUN dihentikan di tengah jalan.")
    else:
        # Jika selesai normal setelah 120 detik
        print("   ✅ Sampai di bawah! Mengirim sinyal balik...")
        client.publish(TOPIC_STATUS, "REACHED_BOTTOM")

def process_return(client):
    """Jalankan ini di thread saat 'return' diterima"""
    print("   ⬆️  Memulai gerakan KEMBALI... (akan memakan waktu 2 menit)")
    
    # Kita asumsikan 'return' tidak bisa diinterupsi
    time.sleep(3)      #####YANG MAU DIGANTI
    
    print("   🏠 Sampai di rumah! Mengirim status STANDBY...")
    client.publish(TOPIC_STATUS, "STANDBY")

# --- Fungsi Callback MQTT ---

def on_connect(client, userdata, flags, rc):
    print(f"✅ Simulator terhubung ke Broker dengan kode {rc}")
    client.subscribe(TOPIC_COMMAND)
    print(f"📡 Simulator sekarang mendengarkan perintah di topik: {TOPIC_COMMAND}")

def on_message(client, userdata, msg):
    global stop_process_event
    command = msg.payload.decode()
    print(f"\n🤖 Perintah diterima: '{command}'")

    if command == "start":
        # Jika ada proses lama, hentikan dulu
        stop_process_event.set()
        # Reset event untuk proses baru
        stop_process_event.clear()
        # Jalankan 'process_start' di thread baru agar tidak memblokir
        threading.Thread(target=process_start, args=(client,)).start()

    elif command == "return":
        # 1. Hentikan proses 'start' yang mungkin sedang berjalan
        stop_process_event.set()
        # 2. Jalankan 'process_return' di thread baru
        threading.Thread(target=process_return, args=(client,)).start()

# --- Program Utama ---
print("--- Robot Simulator v2 (Dengan Threading) Dimulai ---")
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever() # Loop ini sekarang bebas dan selalu mendengarkan
except Exception as e:
    print(f"❌ Gagal terhubung ke broker: {e}")