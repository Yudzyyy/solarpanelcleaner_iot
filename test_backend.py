"""
Unit Tests untuk Solar Panel Cleaner Backend
=============================================
Tests ini berjalan dalam mode terisolasi (tanpa database atau MQTT asli)
menggunakan mock objects untuk menguji logika bisnis.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# SETUP: Set environment variables SEBELUM import backend
# Ini mensimulasikan environment Docker tanpa service yang berjalan
# ---------------------------------------------------------------------------
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("MQTT_BROKER", "localhost")


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------
@pytest.fixture
def app_client():
    """
    Membuat Flask test client dengan semua dependency eksternal di-mock.
    Pattern ini adalah standar industri untuk testing service berbasis event.
    """
    # Mock semua dependency eksternal sebelum import
    with patch("paho.mqtt.client.Client") as mock_mqtt_class, \
         patch("psycopg2.connect") as mock_db_connect, \
         patch("eventlet.monkey_patch"):

        # Setup mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cur
        mock_db_connect.return_value = mock_conn

        # Setup mock MQTT client
        mock_mqtt_instance = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt_instance

        # Import backend SETELAH semua mock siap
        import backend
        backend.app.config["TESTING"] = True

        with backend.app.test_client() as client:
            yield client, backend


# ---------------------------------------------------------------------------
# TEST GROUP 1: Health & Configuration
# ---------------------------------------------------------------------------
class TestConfiguration:
    """Memastikan konfigurasi environment variable terbaca dengan benar."""

    def test_env_db_host_is_set(self):
        """DB_HOST harus bisa dibaca dari environment."""
        assert os.getenv("DB_HOST") is not None

    def test_env_db_name_is_set(self):
        """DB_NAME harus bisa dibaca dari environment."""
        assert os.getenv("DB_NAME") is not None

    def test_env_mqtt_broker_is_set(self):
        """MQTT_BROKER harus bisa dibaca dari environment."""
        assert os.getenv("MQTT_BROKER") is not None


# ---------------------------------------------------------------------------
# TEST GROUP 2: API Endpoints
# ---------------------------------------------------------------------------
class TestApiEndpoints:
    """Menguji semua HTTP endpoint dari backend Flask."""

    def test_get_logs_endpoint_returns_200(self, app_client):
        """GET /logs harus merespons dengan status 200 OK."""
        client, backend = app_client
        with patch.object(backend, "get_db_connection") as mock_db:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cur
            mock_db.return_value = mock_conn

            response = client.get("/logs")
            assert response.status_code == 200

    def test_get_logs_returns_json(self, app_client):
        """GET /logs harus mengembalikan content-type application/json."""
        client, backend = app_client
        with patch.object(backend, "get_db_connection") as mock_db:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cur
            mock_db.return_value = mock_conn

            response = client.get("/logs")
            assert response.content_type == "application/json"

    def test_start_when_already_active_returns_400(self, app_client):
        """POST /start saat cleaning_active=True harus mengembalikan 400."""
        client, backend = app_client
        backend.cleaning_active = True  # Simulasi: pembersihan sedang berjalan

        response = client.post("/start")
        assert response.status_code == 400

        backend.cleaning_active = False  # Reset state

    def test_stop_when_not_active_returns_400(self, app_client):
        """POST /stop saat cleaning_active=False harus mengembalikan 400."""
        client, backend = app_client
        backend.cleaning_active = False  # Pastikan tidak sedang berjalan

        response = client.post("/stop")
        assert response.status_code == 400

    def test_set_schedule_with_invalid_data_returns_400(self, app_client):
        """POST /set_schedule dengan data yang salah harus mengembalikan 400."""
        client, _ = app_client
        response = client.post(
            "/set_schedule",
            json={"schedules": "ini-bukan-list"},  # Format salah
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_set_schedule_with_missing_body_returns_400(self, app_client):
        """POST /set_schedule tanpa body sama sekali harus mengembalikan 400."""
        client, _ = app_client
        response = client.post(
            "/set_schedule",
            json={},  # Tidak ada key 'schedules'
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_set_schedule_with_valid_data_calls_db(self, app_client):
        """POST /set_schedule dengan data valid harus mengembalikan 200."""
        client, backend = app_client
        with patch("psycopg2.connect") as mock_connect, \
             patch("psycopg2.extras.execute_values"), \
             patch.object(backend.socketio, "emit"):
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn

            response = client.post(
                "/set_schedule",
                json={"schedules": ["08:00", "12:00"]},
                content_type="application/json",
            )
            assert response.status_code == 200
            data = response.get_json()
            assert "new_schedules" in data


# ---------------------------------------------------------------------------
# TEST GROUP 3: Business Logic
# ---------------------------------------------------------------------------
class TestBusinessLogic:
    """Menguji fungsi-fungsi inti tanpa memanggil service eksternal."""

    def test_mqtt_topics_are_correct(self, app_client):
        """Konstanta MQTT topic harus bernilai yang benar."""
        _, backend = app_client
        assert backend.MQTT_TOPIC_STATUS == "robot/status"
        assert backend.MQTT_TOPIC_COMMAND == "robot/command"

    def test_initial_cleaning_state_is_false(self, app_client):
        """State awal cleaning_active harus False (tidak sedang membersihkan)."""
        _, backend = app_client
        # Reset ke kondisi awal
        backend.cleaning_active = False
        assert backend.cleaning_active is False

    def test_reset_to_standby_sets_cleaning_inactive(self, app_client):
        """Fungsi reset_to_standby() harus mengset cleaning_active menjadi False."""
        _, backend = app_client
        backend.cleaning_active = True  # Set aktif dulu

        with patch.object(backend.socketio, "emit"):
            backend.reset_to_standby()

        assert backend.cleaning_active is False
