import React, { useState, useEffect } from 'react';
import { Power, Clock, Activity, Edit2, Zap, Leaf, Sun } from 'lucide-react';
import io from 'socket.io-client';

// URL Backend
const BACKEND_URL = 'http://localhost:5000';

export default function SolarPanelCleaner() {
  // --- STATE MANAGEMENT ---
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [systemActive, setSystemActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [directionStatus, setDirectionStatus] = useState('STANDBY');
  const [schedules, setSchedules] = useState([
    { id: 1, time: '06:00', active: true },
    { id: 2, time: '12:00', active: true },
    { id: 3, time: '18:00', active: false }
  ]);
  const [editingId, setEditingId] = useState(null);
  const [tempTime, setTempTime] = useState('');
  const [logs, setLogs] = useState([]);

  // --- SOCKET.IO & API LOGIC ---
  useEffect(() => {
    console.log('🔌 Mencoba koneksi ke:', BACKEND_URL);
    const newSocket = io(BACKEND_URL);

    const fetchInitialLogs = async () => {
      try {
        console.log('📝 Meminta riwayat log dari backend...');
        const response = await fetch(`${BACKEND_URL}/logs`);
        if (!response.ok) throw new Error(`Gagal mengambil data log: ${response.statusText}`);
        const data = await response.json();
        
        const formattedLogs = data.map(log => ({
          id: log.id,
          date: new Date(log.timestamp).toLocaleString('id-ID', { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          action: log.action,
          status: log.status,
          type: log.type
        }));
        
        setLogs(formattedLogs);
        console.log('✅ Riwayat log berhasil dimuat!');
      } catch (error) {
        console.error('❌ Error saat memuat riwayat log:', error);
      }
    };

    newSocket.on('connect', () => {
      console.log('✅ TERHUBUNG ke backend via Socket.IO!');
      setIsConnected(true);
      fetchInitialLogs();
    });

    newSocket.on('disconnect', () => {
      console.log('❌ TERPUTUS dari backend!');
      setIsConnected(false);
    });
    
    newSocket.on('status_update', (data) => {
      setDirectionStatus(data.status);
      if (data.progress !== undefined) setProgress(data.progress);
      setSystemActive(data.status !== 'STANDBY' && data.status !== 'SELESAI');
    });
    
    newSocket.on('progress_update', (data) => {
      setProgress(data.progress);
    });

    newSocket.on('log_update', (data) => {
      const newLog = {
        id: Date.now(),
        date: new Date().toLocaleString('id-ID', { 
          day: '2-digit', 
          month: 'short', 
          year: 'numeric', 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        action: data.action,
        status: data.status,
        type: data.type
      };
      setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 100));
    });

    setSocket(newSocket);

    return () => {
      console.log('🔌 Menutup koneksi socket...');
      newSocket.close();
    };
  }, []);

  // --- API HELPER ---
  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, options);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(errorData.message);
      }
      return await response.json();
    } catch (error) {
      console.error(`❌ Error calling ${endpoint}:`, error);
      alert(`Gagal memanggil API: ${error.message}`);
      throw error;
    }
  };
  
  // --- HANDLER FUNCTIONS ---
  const handleStartCleaning = () => {
    apiCall('/start', { method: 'POST' })
      .then(data => console.log('✅ Response START:', data.message))
      .catch(() => {});
  };

  const handleStopCleaning = () => {
    apiCall('/stop', { method: 'POST' })
      .then(data => console.log('✅ Response STOP:', data.message))
      .catch(() => {});
  };

  const handleSetSchedule = () => {
    const activeSchedules = schedules.filter(s => s.active).map(s => s.time);
    apiCall('/set_schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedules: activeSchedules })
    })
      .then(() => alert('Jadwal berhasil diperbarui di server!'))
      .catch(() => {});
  };

  const handleEditSchedule = (id, currentTime) => {
    setEditingId(id);
    setTempTime(currentTime);
  };

  const handleSaveSchedule = (id) => {
    if (tempTime) {
      setSchedules(schedules.map(s => s.id === id ? { ...s, time: tempTime } : s));
      setEditingId(null);
      setTempTime('');
    }
  };

  const handleToggleSchedule = (id) => {
    setSchedules(schedules.map(s => s.id === id ? { ...s, active: !s.active } : s));
  };

  // --- RENDER ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900 to-teal-900 text-white">
      
      {/* === HERO SECTION === */}
      <div className="relative h-96 overflow-hidden">
        {/* Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-green-700 via-emerald-600 to-teal-700"></div>

        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40" 
          style={{ backgroundImage: `url('/solarpanel.jpg')` }}
        ></div>

        {/* SVG Mountain Pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-5" viewBox="0 0 1440 400" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{stopColor: '#065f46', stopOpacity: 0.8}} />
              <stop offset="100%" style={{stopColor: '#047857', stopOpacity: 0.6}} />
            </linearGradient>
          </defs>
          <path fill="url(#grad1)" d="M0,160 Q240,100 480,140 T960,120 T1440,160 L1440,400 L0,400 Z" />
          <path fill="rgba(5, 150, 105, 0.4)" d="M0,200 Q360,140 720,180 T1440,200 L1440,400 L0,400 Z" />
        </svg>

        {/* Decorative Icons */}
        <div className="absolute inset-0 overflow-hidden opacity-20">
          <Zap className="absolute top-20 right-1/4 text-white animate-pulse" size={60} style={{animationDuration: '3s'}} />
          <Sun className="absolute top-32 left-1/3 text-yellow-200 animate-pulse" size={70} style={{animationDuration: '4s'}} />
          <Leaf className="absolute bottom-32 right-1/3 text-green-200" size={50} />
        </div>
        
        {/* Dark Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-900/20 to-emerald-900/60"></div>

        {/* Connection Status Badge */}
        <div className="absolute top-6 right-6 z-20">
          <div className={`backdrop-blur-md border rounded-full px-6 py-3 flex items-center gap-2 shadow-lg transition-colors ${
            isConnected 
              ? 'bg-emerald-500/30 border-emerald-300/50' 
              : 'bg-red-500/30 border-red-400/50'
          }`}>
            <div className={`w-2 h-2 rounded-full animate-pulse shadow-lg ${
              isConnected 
                ? 'bg-emerald-300 shadow-emerald-400' 
                : 'bg-red-300 shadow-red-400'
            }`}></div>
            <span className={`font-semibold ${isConnected ? 'text-white' : 'text-red-200'}`}>
              {isConnected ? 'Terhubung' : 'Terputus'}
            </span>
          </div>
        </div>

        {/* Hero Title */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-8">
          <div className="flex items-center justify-center gap-4 mb-4">
            <Sun className="text-yellow-300" size={52} />
            <h1 className="text-6xl md:text-7xl font-black text-white drop-shadow-2xl">
              Solar Panel Cleaner
            </h1>
            <Leaf className="text-green-300" size={52} />
          </div>
          <p className="text-white/90 text-xl md:text-2xl font-light max-w-3xl drop-shadow-lg">
            Dashboard kontrol dan monitoring sistem pembersih otomatis
          </p>
        </div>

        {/* Wave Separator */}
        <div className="absolute bottom-0 left-0 right-0 z-10">
          <svg viewBox="0 0 1440 120" className="w-full h-16" preserveAspectRatio="none">
            <path fill="#064e3b" d="M0,64L48,69.3C96,75,192,85,288,80C384,75,480,53,576,48C672,43,768,53,864,58.7C960,64,1056,64,1152,58.7C1248,53,1344,43,1392,37.3L1440,32L1440,120L1392,120C1344,120,1248,120,1152,120C1056,120,960,120,864,120C768,120,672,120,576,120C480,120,384,120,288,120C192,120,96,120,48,120L0,120Z"></path>
          </svg>
        </div>
      </div>

      {/* === MAIN CONTENT SECTION === */}
      <div className="relative bg-gradient-to-br from-emerald-900 via-teal-800 to-green-900 px-4 md:px-8 pb-12 -mt-1">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10 pt-8">
          
          {/* --- CARD 1: Kontrol Sistem --- */}
          <div className="bg-gradient-to-br from-blue-900/50 to-cyan-900/40 backdrop-blur-xl rounded-3xl p-8 border-2 border-blue-400/30 shadow-2xl hover:shadow-blue-500/30 transition-all">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-gradient-to-br from-emerald-500 to-green-600 p-3 rounded-2xl shadow-lg">
                <Power className="text-white" size={28} />
              </div>
              <h2 className="text-3xl font-bold text-white">Kontrol Sistem</h2>
            </div>

            <div className="space-y-6">
              {/* Status */}
              <div>
                <p className="text-white text-sm mb-3 uppercase tracking-wide">Status Saat Ini</p>
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full transition-colors ${
                    systemActive ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                  }`}></div>
                  <span className={`text-3xl font-bold transition-colors ${
                    systemActive ? 'text-green-300' : 'text-gray-300'
                  }`}>
                    {directionStatus}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <p className="text-white text-sm uppercase tracking-wide">Progress Pembersihan</p>
                  <span className="text-2xl font-bold text-emerald-300">{Math.round(progress)}%</span>
                </div>
                <div className="bg-emerald-950/50 rounded-full h-4 overflow-hidden border border-emerald-600/30">
                  <div 
                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-300 shadow-lg shadow-green-500/50"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Control Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  onClick={handleStartCleaning}
                  disabled={systemActive || !isConnected}
                  className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-green-500/50"
                >
                  <Zap size={20} />
                  MULAI
                </button>
                <button
                  onClick={handleStopCleaning}
                  disabled={!systemActive || !isConnected}
                  className="flex-1 bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-red-500/50"
                >
                  STOP
                </button>
              </div>
            </div>
          </div>

          {/* --- CARD 2: Jadwal Otomatis --- */}
          <div className="bg-gradient-to-br from-blue-900/50 to-cyan-900/40 backdrop-blur-xl rounded-3xl p-8 border-2 border-blue-400/30 shadow-2xl hover:shadow-blue-500/30 transition-all">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-gradient-to-br from-cyan-500 to-blue-600 p-3 rounded-2xl shadow-lg">
                <Clock className="text-white" size={28} />
              </div>
              <h2 className="text-3xl font-bold text-white">Jadwal Otomatis</h2>
            </div>

            <div className="space-y-4 mb-6">
              {schedules.map((schedule) => (
                <div 
                  key={schedule.id} 
                  className="bg-teal-950/40 rounded-xl p-4 border border-teal-600/30 flex items-center justify-between hover:bg-teal-900/40 transition-all"
                >
                  <div className="flex items-center gap-4">
                    <input 
                      type="checkbox" 
                      checked={schedule.active} 
                      onChange={() => handleToggleSchedule(schedule.id)} 
                      className="w-6 h-6 rounded border-2 border-teal-500 bg-teal-950 text-cyan-500 focus:ring-cyan-500"
                    />
                    {editingId === schedule.id ? (
                      <input 
                        type="time" 
                        value={tempTime} 
                        onChange={(e) => setTempTime(e.target.value)} 
                        className="bg-slate-700 text-white px-3 py-1 rounded-lg border border-cyan-500 outline-none"
                      />
                    ) : (
                      <span className="text-white font-semibold text-lg">
                        Jadwal {schedule.id}: {schedule.time}
                      </span>
                    )}
                  </div>
                  {editingId === schedule.id ? (
                    <button 
                      onClick={() => handleSaveSchedule(schedule.id)} 
                      className="bg-green-500 hover:bg-green-600 text-white p-2 rounded-lg transition-all"
                    >
                      ✓
                    </button>
                  ) : (
                    <button 
                      onClick={() => handleEditSchedule(schedule.id, schedule.time)} 
                      className="bg-cyan-500 hover:bg-cyan-600 text-white p-2 rounded-lg transition-all"
                    >
                      <Edit2 size={18} />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <button 
              onClick={handleSetSchedule} 
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-cyan-500/50"
            >
              ATUR JADWAL
            </button>
          </div>

          {/* --- CARD 3: Log Aktivitas --- */}
          <div className="bg-gradient-to-br from-blue-900/50 to-cyan-900/40 backdrop-blur-xl rounded-3xl p-8 border-2 border-blue-400/30 shadow-2xl hover:shadow-blue-500/30 transition-all">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-gradient-to-br from-emerald-500 to-green-600 p-3 rounded-2xl shadow-lg">
                <Activity className="text-white" size={28} />
              </div>
              <h2 className="text-3xl font-bold text-white">Log Aktivitas</h2>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {logs.length > 0 ? (
                logs.map((log) => (
                  <div
                    key={log.id}
                    className={`p-4 rounded-xl text-white shadow-md hover:scale-[1.02] transition-all ${
                      log.type === 'stop' 
                        ? 'bg-gradient-to-r from-red-500 to-pink-600' :
                      log.type === 'complete' 
                        ? 'bg-gradient-to-r from-blue-500 to-cyan-600' :
                      log.type === 'start' || log.type === 'auto' 
                        ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
                        'bg-gray-700'
                    }`}
                  >
                    <p className="text-gray-200 text-sm mb-1">{log.date}</p>
                    <p className="font-bold text-lg">{log.action}</p>
                    <p className="text-sm opacity-90">Status: {log.status}</p>
                  </div>
                ))
              ) : (
                <p className="text-center text-emerald-400/70">Tidak ada aktivitas.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}