# PERBAIKAN FINAL: Tambahkan ini di baris paling atas!
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import threading # Diimpor hanya untuk Event
import datetime
import psycopg2
import psycopg2.extras
import os
import paho.mqtt.client as mqtt

# --- KONFIGURASI ---
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

# --- VARIABEL GLOBAL ---
cleaning_active = False
stop_event = threading.Event()
reverse_event = threading.Event()

# --- FUNGSI DATABASE & LOGGING ---
def get_db_connection():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

def log_and_emit(action, status, type):
    conn = None; cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO logs (action, status, type) VALUES (%s, %s, %s)", (action, status, type))
        conn.commit()
    except Exception as e:
        print(f"❌ [DB] Gagal menyimpan log: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    socketio.emit('log_update', {'action': action, 'status': status, 'type': type})

def load_schedules_from_db():
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

# --- ROUTES / ENDPOINTS ---
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
        return jsonify({'message': 'Jadwal berhasil diperbarui', 'new_schedules': new_schedules})
    except Exception as e:
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
    socketio.start_background_task(target=run_cleaning_cycle)
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

# --- JEMBATAN MQTT ---
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip() 
    
    # PERUBAHAN: Tangani pesan progres dari Arduino
    if payload.startswith("P:"):
        try:
            # Ambil nilai progres (misal dari "P:15" menjadi 15)
            progress_value = int(payload.split(':')[1])
            # Langsung kirim ke UI
            socketio.emit('progress_update', {'progress': progress_value})
        except (IndexError, ValueError):
            print(f"⚠️ Pesan progres tidak valid: {payload}")
        return # Hentikan proses di sini untuk pesan progres

    # Sisa logika tetap sama
    if payload == "REACHED_BOTTOM":
        reverse_event.set()
    elif payload == "STANDBY":
        reset_to_standby()
    elif payload == "SELESAI":
        reset_to_standby()

def mqtt_bridge_thread():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e: print(f"❌ [MQTT Bridge] Gagal terhubung ke broker: {e}")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

# --- FUNGSI UTAMA ---
def run_cleaning_cycle():
    global cleaning_active
    print("\n🚀 [SISTEM] MEMULAI SIKLUS PEMBERSIHAN")
    try:
        # PERUBAHAN: Hapus semua loop 'for progress'
        print("⬇️  [FASE 1] Menunggu robot bergerak TURUN...")
        socketio.emit('status_update', {'status': 'TURUN', 'progress': 0})
        log_and_emit('START MANUAL', 'SUCCESS', 'start')
        
        # Cukup tunggu sinyal 'REACHED_BOTTOM', progress akan diupdate oleh on_message
        while not reverse_event.is_set():
            if stop_event.is_set(): print("⏹️  Proses dihentikan saat fase TURUN"); return
            socketio.sleep(0.1)
        
        print("✅ Sinyal balik diterima! Melanjutkan...")
        print("🚀 [MQTT] Mengirim perintah 'naik' ke robot...")
        mqtt_client.publish(MQTT_TOPIC_COMMAND, "naik")
        print("⬆️  [FASE 3] Menunggu robot bergerak NAIK...")
        socketio.emit('status_update', {'status': 'NAIK', 'progress': 50})
        
        # Di sini thread hanya menunggu sampai 'stop' ditekan. 
        # Sinyal 'SELESAI' dari robot akan memicu reset.
        while not stop_event.is_set():
             socketio.sleep(0.5)

    except Exception as e: print(f"❌ [ERROR] Terjadi kesalahan dalam siklus: {e}"); reset_to_standby()
    finally:
        cleaning_active = False
        print("✅ [SISTEM] Siklus pembersihan selesai atau dihentikan.\n")

def reset_to_standby():
    global cleaning_active
    cleaning_active = False
    socketio.emit('status_update', {'status': 'STANDBY', 'progress': 0})

def schedule_checker():
    global cleaning_active
    while True:
        try:
            current_db_schedules = load_schedules_from_db()
            now = datetime.datetime.now().strftime("%H:%M")
            if now in current_db_schedules and not cleaning_active:
                print(f"⏰ [AUTO] Menjalankan pembersihan otomatis ({now})")
                log_and_emit('START AUTO', 'SUCCESS', 'auto')
                stop_event.clear(); reverse_event.clear(); cleaning_active = True
                mqtt_client.publish(MQTT_TOPIC_COMMAND, "start")
                socketio.start_background_task(target=run_cleaning_cycle)
        except Exception as e: print(f"❌ [SCHEDULER] Error: {e}")
        socketio.sleep(5)

# --- MAIN SERVER ---
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

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("✅ [MQTT Client] Terhubung ke broker.")
    except Exception as e: print(f"❌ [MQTT Client] Gagal terhubung: {e}")

    socketio.start_background_task(target=mqtt_bridge_thread)
    socketio.start_background_task(target=schedule_checker)
    
    print("\n🚀 SOLAR PANEL CLEANER BACKEND v6.0 (Hardware Driven)\n")
    
    socketio.run(app, host='0.0.0.0', port=5000)

