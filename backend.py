import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import threading
import datetime
import psycopg2
import psycopg2.extras
import os
import paho.mqtt.client as mqtt

# --- KONFIGURASI (MEMBACA DARI DOCKER ENVIRONMENT) ---
DB_NAME = os.getenv("DB_NAME", "solar_cleaner_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ttz")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = "robot/status"
MQTT_TOPIC_COMMAND = "robot/command"

# --- INISIALISASI APLIKASI ---
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ===============================
# VARIABEL GLOBAL
# ===============================
cleaning_active = False
stop_event = threading.Event()
reverse_event = threading.Event()

# ===============================
# FUNGSI-FUNGSI DATABASE & LOGGING
# ===============================
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

def log_and_emit(action, status, type):
    """Menyimpan log ke database DAN mengirimnya ke klien via Socket.IO."""
    conn = None; cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO logs (action, status, type) VALUES (%s, %s, %s)", (action, status, type))
        conn.commit()
        print(f"📝 [DB] Log disimpan: {action} - {status}")
    except Exception as e:
        print(f"❌ [DB] Gagal menyimpan log: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    socketio.emit('log_update', {'action': action, 'status': status, 'type': type})

def load_schedules_from_db():
    """Membaca semua jadwal dari database dan mengembalikannya sebagai list."""
    schedules = []; conn = None; cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT time_setting FROM schedules ORDER BY time_setting ASC")
        rows = cur.fetchall()
        schedules = [row[0] for row in rows]
    except Exception as e:
        print(f"❌ [DB] Gagal memuat jadwal: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return schedules

# ===============================
# ROUTES / ENDPOINTS
# ===============================
@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    conn = None; cur = None
    try:
        data = request.json
        new_schedules = data.get('schedules')
        if new_schedules is None or not isinstance(new_schedules, list): return jsonify({'message': "Format data salah"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM schedules")
        if new_schedules:
            insert_data = [(time_str,) for time_str in new_schedules]
            psycopg2.extras.execute_values(cur, "INSERT INTO schedules (time_setting) VALUES %s", insert_data)
        conn.commit()
        log_and_emit('SET JADWAL', 'SUCCESS', 'schedule')
        print(f"🔄 [JADWAL] Jadwal di database diperbarui menjadi: {new_schedules}")
        return jsonify({'message': 'Jadwal berhasil diperbarui', 'new_schedules': new_schedules})
    except Exception as e:
        print(f"❌ [JADWAL] Error saat update jadwal DB: {e}")
        if conn: conn.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
         if cur: cur.close()
         if conn: conn.close()

@app.route('/start', methods=['POST'])
def start_cleaning():
    global cleaning_active
    if cleaning_active: return jsonify({'message': 'Proses pembersihan sudah berjalan'}), 400
    stop_event.clear(); reverse_event.clear(); cleaning_active = True
    print("🚀 [MQTT] Mengirim perintah 'start' ke robot...")
    mqtt_client.publish(MQTT_TOPIC_COMMAND, "start")
    socketio.start_background_task(target=run_cleaning_cycle, action='START MANUAL', type='start')
    print("✅ Request START diterima, tugas latar belakang dimulai")
    return jsonify({'message': 'Pembersihan dimulai'})

@app.route('/stop', methods=['POST'])
def stop_cleaning():
    if not cleaning_active: return jsonify({'message': 'Tidak sedang berjalan'}), 400
    print("⏹️ Request STOP diterima, memerintahkan robot untuk kembali...")
    stop_event.set() 
    mqtt_client.publish(MQTT_TOPIC_COMMAND, "return")
    socketio.emit('status_update', {'status': 'KEMBALI KE AWAL'})
    log_and_emit('STOP MANUAL', 'SUCCESS', 'stop')
    return jsonify({'message': 'Robot diperintahkan untuk kembali ke awal'})

@app.route('/logs', methods=['GET'])
def get_logs():
    logs = []; conn = None; cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, timestamp::text, action, status, type FROM logs ORDER BY timestamp DESC LIMIT 100")
        logs = cur.fetchall()
    except Exception as e: print(f"❌ [DB] Gagal memuat log: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return jsonify(logs)

# ===============================
# JEMBATAN MQTT (Logika Dipindahkan ke Klien Global)
# ===============================
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"✅ [MQTT] Terhubung ke Broker dengan kode {rc}")
    client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip() 
    
    # Menangani pesan progres
    if payload.startswith("P:"):
        try:
            progress_value = int(payload.split(':')[1])
            socketio.emit('progress_update', {'progress': progress_value})
            print(f"📊 Progress: {progress_value}%")
        except (IndexError, ValueError):
            print(f"⚠️ Pesan progres tidak valid: {payload}")
        return 

    # Menangani pesan status
    print(f"📬 [MQTT] Menerima pesan: '{payload}'")
    
    # TAMBAHAN: Emit status ke frontend untuk setiap perubahan status
    if payload == "TURUN":
        socketio.emit('status_update', {'status': 'TURUN'})
    elif payload == "NAIK":
        socketio.emit('status_update', {'status': 'NAIK'})
    elif payload == "KEMBALI":
        socketio.emit('status_update', {'status': 'KEMBALI'})
    elif payload == "REACHED_BOTTOM":
        print("🚀 [MQTT] Sinyal balik terdeteksi!")
        reverse_event.set()
    elif payload == "STANDBY":
        print("🏠 [MQTT] Robot sudah di posisi awal!")
        reset_to_standby()
        log_and_emit('STOP COMPLETE', 'SUCCESS', 'stop')  # TAMBAHAN: Log stop complete
    elif payload == "SELESAI":
        print("🎉 [MQTT] Robot selesai pembersihan!")
        reset_to_standby()
        log_and_emit('PEMBERSIHAN SELESAI', 'SUCCESS', 'complete')  # TAMBAHAN: Log complete

# ===============================
# FUNGSI-FUNGSI UTAMA
# ===============================
def run_cleaning_cycle(action, type):
    global cleaning_active
    print("\n" + "="*60 + "\n🚀 [SISTEM] MEMULAI SIKLUS PEMBERSIHAN")
    try:
        print("⬇️  [FASE 1] Menunggu robot bergerak TURUN...")
        socketio.emit('status_update', {'status': 'TURUN', 'progress': 0})
        log_and_emit(action, 'SUCCESS', type)
        
        while not reverse_event.is_set():
            if stop_event.is_set(): 
                print("⏹️  [SISTEM] Proses dihentikan saat fase TURUN")
                return
            socketio.sleep(0.1)
        
        print("✅ [SISTEM] Sinyal balik diterima! Melanjutkan...")
        print("🚀 [MQTT] Mengirim perintah 'naik' ke robot...")
        mqtt_client.publish(MQTT_TOPIC_COMMAND, "naik")
        
        print("⬆️  [FASE 3] Menunggu robot bergerak NAIK...")
        socketio.emit('status_update', {'status': 'NAIK', 'progress': 50})
        
        # PERUBAHAN: Tidak perlu while loop lagi
        # Arduino akan kirim "SELESAI" dan di-handle di on_message()
        
    except Exception as e: 
        print(f"❌ [ERROR] Terjadi kesalahan dalam siklus: {e}")
        reset_to_standby()
    finally:
        cleaning_active = False
        print("="*60 + "\n✅ [SISTEM] Siklus pembersihan selesai atau dihentikan.\n" + "="*60 + "\n")

def reset_to_standby():
    global cleaning_active
    cleaning_active = False
    socketio.emit('status_update', {'status': 'STANDBY', 'progress': 0})
    print("🔄 [SISTEM] Reset ke STANDBY")

def schedule_checker():
    global cleaning_active
    last_executed_minute = None  # ✅ Variabel untuk track menit terakhir
    
    while True:
        try:
            current_db_schedules = load_schedules_from_db()
            now = datetime.datetime.now().strftime("%H:%M")
            
            # ✅ CEK: Apakah sudah dijalankan di menit ini?
            if now in current_db_schedules and not cleaning_active and now != last_executed_minute:
                print(f"⏰ [AUTO] Menjalankan pembersihan otomatis ({now})")
                stop_event.clear(); reverse_event.clear(); cleaning_active = True
                last_executed_minute = now  # ✅ TANDAI bahwa menit ini sudah dijalankan
                
                print("🚀 [MQTT] Mengirim perintah 'start' ke robot (via Jadwal)...")
                mqtt_client.publish(MQTT_TOPIC_COMMAND, "start")
                socketio.start_background_task(target=run_cleaning_cycle, action='START AUTO', type='auto')
            
            # ✅ RESET jika sudah ganti menit (agar bisa jalan lagi di jadwal berikutnya)
            elif now != last_executed_minute:
                # Menit sudah berganti, reset tracker
                pass
                
        except Exception as e: 
            print(f"❌ [SCHEDULER] Error: {e}")
        
        socketio.sleep(5)

# ===============================
# MAIN SERVER
# ===============================
if __name__ == '__main__':
    print("⏳ Menunggu database siap...")
    time.sleep(10)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS schedules (id SERIAL PRIMARY KEY, time_setting VARCHAR(5) NOT NULL UNIQUE);")
        cur.execute("CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(), action VARCHAR(255) NOT NULL, status VARCHAR(50) NOT NULL, type VARCHAR(50));")
        conn.commit()
        cur.close(); conn.close()
        print("✅ [DB] Tabel 'schedules' dan 'logs' siap.")
    except Exception as e: print(f"❌ [DB] Gagal inisialisasi tabel: {e}")

    # Atur callback untuk klien MQTT
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() # Jalankan loop di thread terpisah (non-blocking)
        print("✅ [MQTT Client] Terhubung dan mendengarkan di thread terpisah.")
    except Exception as e: print(f"❌ [MQTT Client] Gagal terhubung: {e}")

    socketio.start_background_task(target=schedule_checker)
    
    print("\n" + "="*60 + "\n🚀 SOLAR PANEL CLEANER BACKEND v7.0 (Non-Blocking MQTT)\n" + "="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000)
