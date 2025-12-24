import React, { useEffect, useState } from 'react';
// ...existing code...
import styles from './Admin.module.css';
import { fetchCinemas } from '../Cinemas/CinemaLogic';
import type { Cinema } from '../Cinemas/CinemaLogic';
import { fetchAuditoriumsByCinemaId } from './Utils/AuditoriumApi';

interface AuditoriumRow {
  id: number;
  name: string;
  pattern: string;
}

export default function RoomManage() {
  const [cinemas, setCinemas] = useState<Cinema[]>([]);
  const [selectedCinemaId, setSelectedCinemaId] = useState<number | null>(null);
  const [auditoriums, setAuditoriums] = useState<AuditoriumRow[]>([]);
  const [loadingCinemas, setLoadingCinemas] = useState(true);
  const [loadingRooms, setLoadingRooms] = useState(false);
  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [showAddPopup, setShowAddPopup] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomPattern, setNewRoomPattern] = useState<'ONE'|'TWO'|'THREE'>('ONE');
  // const [addingRoom, setAddingRoom] = useState(false); // No longer needed
  const [optimisticRooms, setOptimisticRooms] = useState<AuditoriumRow[]>([]);
  const [deletingRoomIds, setDeletingRoomIds] = useState<number[]>([]);
  const [optimisticDeleteRooms, setOptimisticDeleteRooms] = useState<AuditoriumRow[]>([]);
  const [editingPatternId, setEditingPatternId] = useState<number|null>(null);
  const [editingPatternValue, setEditingPatternValue] = useState<'ONE'|'TWO'|'THREE'>('ONE');
  const [savingPatternIds, setSavingPatternIds] = useState<number[]>([]);
    // Edit pattern handler
    const handleEditPattern = (room: AuditoriumRow) => {
      setEditingPatternId(room.id);
      setEditingPatternValue(room.pattern as 'ONE'|'TWO'|'THREE');
    };

    const handleCancelEditPattern = () => {
      setEditingPatternId(null);
    };

    const handleSavePattern = async (room: AuditoriumRow) => {
      setSavingPatternIds(prev => [...prev, room.id]);
      setEditingPatternId(null);
      // Optimistically disable row
      setOptimisticDeleteRooms(prev => [room, ...prev]);
      setAuditoriums(prev => prev.filter(r => r.id !== room.id));
      try {
        const token = localStorage.getItem('access-token');
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        await fetch(`https://cinema.cegove.cloud/auditoriums/${room.id}/pattern`, {
          method: 'PUT',
          headers,
          body: editingPatternValue, // send as plain string, not JSON
        });
        await reloadRooms(selectedCinemaId);
      } catch (e) {
        // Optionally show error
      } finally {
        setSavingPatternIds(prev => prev.filter(id => id !== room.id));
        setOptimisticDeleteRooms(prev => prev.filter(r => r.id !== room.id));
      }
    };
  // Delete room handler
  const handleDeleteRoom = async (roomId: number) => {
    // Find the room info to show spinner row
    const room = auditoriums.find(r => r.id === roomId);
    if (!room) return;
    setDeletingRoomIds(prev => [...prev, roomId]);
    setOptimisticDeleteRooms(prev => [room, ...prev]);
    setAuditoriums(prev => prev.filter(r => r.id !== roomId));
    try {
      const token = localStorage.getItem('access-token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await fetch(`https://cinema.cegove.cloud/auditoriums/${roomId}`, {
        method: 'DELETE',
        headers,
      });
      // Reload rooms after delete
      await reloadRooms(selectedCinemaId);
    } catch (e) {
      // Optionally show error
    } finally {
      setDeletingRoomIds(prev => prev.filter(id => id !== roomId));
      setOptimisticDeleteRooms(prev => prev.filter(r => r.id !== roomId));
    }
  };

  // Function to reload rooms
  const reloadRooms = async (cinemaId: number|null) => {
    if (!cinemaId) {
      setAuditoriums([]);
      return;
    }
    setLoadingRooms(true);
    try {
      const rooms = await fetchAuditoriumsByCinemaId(cinemaId);
      if (Array.isArray(rooms)) {
        setAuditoriums(rooms);
      } else if (rooms && typeof rooms === 'object') {
        setAuditoriums([rooms]);
      } else {
        setAuditoriums([]);
      }
    } catch (e) {
      setAuditoriums([]);
    } finally {
      setLoadingRooms(false);
    }
  };

  useEffect(() => {
    async function loadCinemas() {
      setLoadingCinemas(true);
      try {
        const cinemaList = await fetchCinemas();
        setCinemas(cinemaList);
        // Lấy danh sách thành phố từ cinemas
        const cityList = Array.from(new Set(cinemaList.map(c => c.city).filter(Boolean)));
        setCities(cityList);
      } catch (e) {
        setCinemas([]);
        setCities([]);
      } finally {
        setLoadingCinemas(false);
      }
    }
    loadCinemas();
  }, []);

  useEffect(() => {
    reloadRooms(selectedCinemaId);
  }, [selectedCinemaId]);

  // Popup for adding room
  const handleAddRoom = async () => {
    if (!selectedCinemaId || !newRoomName) return;
    setShowAddPopup(false);
    // setAddingRoom(true); // No longer needed
    // Create optimistic room with unique temp id
    const optimistic: AuditoriumRow = {
      id: Date.now() + Math.floor(Math.random() * 10000), // unique temp id
      name: newRoomName,
      pattern: newRoomPattern,
    };
    setOptimisticRooms(prev => [optimistic, ...prev]);
    // POST request with token
    try {
      const token = localStorage.getItem('access-token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`https://cinema.cegove.cloud/cinemas/${selectedCinemaId}/auditoriums`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name: newRoomName, pattern: newRoomPattern }),
      });
      const data = await res.json();
      // Remove this optimistic room regardless of success
      setOptimisticRooms(prev => prev.filter(r => r.id !== optimistic.id));
      if (data && data.id) {
        await new Promise(r => setTimeout(r, 0));
        await reloadRooms(selectedCinemaId); // Reload room list after success
      }
    } catch (e) {
      setOptimisticRooms(prev => prev.filter(r => r.id !== optimistic.id));
    } finally {
      setNewRoomName('');
      setNewRoomPattern('ONE');
    }
  };

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>Quản lý phòng</h1>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16, justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <label htmlFor="city-select" style={{ fontWeight: 500 }}>Chọn thành phố:</label>
          <select
            id="city-select"
            value={selectedCity}
            onChange={e => setSelectedCity(e.target.value)}
            style={{ padding: 8, borderRadius: 6, border: '1px solid #bbb', minWidth: 180 }}
          >
            <option value="">-- Chọn thành phố --</option>
            {cities.map(city => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
          <label htmlFor="cinema-select" style={{ fontWeight: 500 }}>Chọn rạp:</label>
          <select
            id="cinema-select"
            value={selectedCinemaId ?? ''}
            onChange={e => setSelectedCinemaId(e.target.value ? Number(e.target.value) : null)}
            style={{ padding: 8, borderRadius: 6, border: '1px solid #bbb', minWidth: 180 }}
          >
            <option value="">-- Chọn rạp --</option>
            {cinemas.filter(c => !selectedCity || c.city === selectedCity).map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <button className={styles.btnPrimary} disabled={!selectedCinemaId} onClick={() => setShowAddPopup(true)}>+ Thêm phòng</button>
      </div>
      {/* Add Room Popup */}
      {showAddPopup && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.2)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', padding: 32, borderRadius: 12, minWidth: 320, boxShadow: '0 2px 16px #0002', display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h2 style={{ margin: 0 }}>Thêm phòng mới</h2>
            <div>Rạp: <b>{cinemas.find(c => c.id === selectedCinemaId)?.name || ''}</b></div>
            <div>
              <label>Tên phòng:</label>
              <input type="text" value={newRoomName} onChange={e => setNewRoomName(e.target.value)} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #bbb' }} />
            </div>
            <div>
              <label>Pattern:</label>
              <div style={{ display: 'flex', gap: 12 }}>
                {['ONE','TWO','THREE'].map(p => (
                  <label key={p} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input type="radio" checked={newRoomPattern === p} onChange={() => setNewRoomPattern(p as any)} /> {p}
                  </label>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowAddPopup(false)} style={{ padding: '8px 20px', borderRadius: 6, border: '1px solid #bbb', background: '#eee' }}>Hủy</button>
              <button className={styles.btnPrimary} disabled={!newRoomName} onClick={handleAddRoom}>Tạo phòng</button>
            </div>
          </div>
        </div>
      )}
      {loadingCinemas ? (
        <div>Đang tải danh sách rạp...</div>
      ) : loadingRooms ? (
        <div>Đang tải danh sách phòng...</div>
      ) : (
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ textAlign: 'center' }}>ID</th>
                <th style={{ textAlign: 'center' }}>Tên phòng</th>
                <th style={{ textAlign: 'center' }}>Pattern</th>
                <th style={{ textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {selectedCinemaId == null ? (
                <tr><td colSpan={4} style={{ textAlign: 'center', color: '#888' }}>Vui lòng chọn rạp</td></tr>
              ) : (
                <>
                  {optimisticRooms.map(room => (
                    <tr key={room.id} style={{ opacity: 0.5, pointerEvents: 'none' }}>
                      <td style={{ textAlign: 'center' }}>
                        <span style={{
                          display: 'inline-block',
                          width: 20,
                          height: 20,
                          border: '3px solid #ccc',
                          borderTop: '3px solid #1976d2',
                          borderRadius: '50%',
                          animation: 'spin 1s linear infinite',
                        }} />
                        <style>{`@keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }`}</style>
                      </td>
                      <td style={{ textAlign: 'center' }}>{room.name}</td>
                      <td style={{ textAlign: 'center' }}>{room.pattern}</td>
                      <td style={{ textAlign: 'center' }}><span>Đang tạo phòng...</span></td>
                    </tr>
                  ))}
                  {optimisticDeleteRooms.map(room => {
                    // If this row is being saved for pattern, show 'Đang lưu...'; if being deleted, show 'Đang xóa...'
                    const isSavingPattern = savingPatternIds.includes(room.id);
                    return (
                      <tr key={room.id} style={{ opacity: 0.5, pointerEvents: 'none' }}>
                        <td style={{ textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-block',
                            width: 20,
                            height: 20,
                            border: '3px solid #ccc',
                            borderTop: isSavingPattern ? '#1976d2' : '#d32f2f',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                          }} />
                          <style>{`@keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }`}</style>
                        </td>
                        <td style={{ textAlign: 'center', color: '#888' }}>{room.name}</td>
                        <td style={{ textAlign: 'center', color: '#888' }}>{room.pattern}</td>
                        <td style={{ textAlign: 'center', color: '#888' }}>{isSavingPattern ? 'Đang lưu...' : 'Đang xóa...'}</td>
                      </tr>
                    );
                  })}
                  {auditoriums.length === 0 && optimisticDeleteRooms.length === 0 ? (
                    <tr><td colSpan={4} style={{ textAlign: 'center', color: '#888' }}>Không có phòng nào</td></tr>
                  ) : (
                    auditoriums.map(room => {
                      const isEditing = editingPatternId === room.id;
                      const isSaving = savingPatternIds.includes(room.id);
                      if (isSaving) {
                        // Show disabled row with spinner while saving
                        return (
                          <tr key={room.id} style={{ opacity: 0.5, pointerEvents: 'none' }}>
                            <td style={{ textAlign: 'center' }}>
                              <span style={{
                                display: 'inline-block',
                                width: 20,
                                height: 20,
                                border: '3px solid #ccc',
                                borderTop: '3px solid #1976d2',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                              }} />
                              <style>{`@keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }`}</style>
                            </td>
                            <td style={{ textAlign: 'center', color: '#888' }}>{room.name}</td>
                            <td style={{ textAlign: 'center', color: '#888' }}>{room.pattern}</td>
                            <td style={{ textAlign: 'center', color: '#888' }}>Đang lưu...</td>
                          </tr>
                        );
                      }
                      return (
                        <tr key={room.id} style={isEditing ? { opacity: 1 } : {}}>
                          <td style={{ textAlign: 'center' }}>{room.id}</td>
                          <td style={{ textAlign: 'center' }}>{room.name}</td>
                          <td style={{ textAlign: 'center' }}>
                            {isEditing ? (
                              <select
                                value={editingPatternValue}
                                onChange={e => setEditingPatternValue(e.target.value as 'ONE'|'TWO'|'THREE')}
                                style={{ padding: 6, borderRadius: 6, border: '1px solid #bbb', minWidth: 80 }}
                                disabled={isSaving}
                              >
                                <option value="ONE">ONE</option>
                                <option value="TWO">TWO</option>
                                <option value="THREE">THREE</option>
                              </select>
                            ) : (
                              room.pattern
                            )}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {isEditing ? (
                              <>
                                <button
                                  className={styles.btnPrimary}
                                  style={{ marginRight: 8, padding: '4px 12px', borderRadius: 4 }}
                                  onClick={() => handleSavePattern(room)}
                                  disabled={isSaving}
                                >Lưu</button>
                                <button
                                  style={{ border: '1px solid #000', borderRadius: 4, padding: '4px 12px', background: 'white', color: '#000' }}
                                  onClick={handleCancelEditPattern}
                                  disabled={isSaving}
                                >Hủy</button>
                              </>
                            ) : (
                              <>
                                <button
                                  style={{ marginRight: 8, border: '1px solid #000', borderRadius: 4, padding: '4px 12px', background: 'white', color: '#000', cursor: 'pointer' }}
                                  onClick={() => handleEditPattern(room)}
                                  disabled={editingPatternId !== null || savingPatternIds.length > 0}
                                >Sửa pattern</button>
                                <button
                                  style={{ border: '1px solid #000', borderRadius: 4, padding: '4px 12px', background: 'white', color: '#000', cursor: 'pointer', minWidth: 60 }}
                                  onClick={() => handleDeleteRoom(room.id)}
                                  disabled={editingPatternId !== null || savingPatternIds.length > 0}
                                >Xóa</button>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );  
}
