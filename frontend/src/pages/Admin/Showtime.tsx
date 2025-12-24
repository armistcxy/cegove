import React, { useEffect, useState } from 'react';
import styles from './Admin.module.css';
import { fetchCinemas } from '../Cinemas/CinemaLogic';
import type { Cinema } from '../Cinemas/CinemaLogic';

interface Showtime {
  id: string;
  movie_id: string;
  cinema_id: string;
  auditorium_id: string;
  start_time: string;
  end_time: string;
  base_price: number;
}



export default function ShowtimeManage() {
  const [cinemas, setCinemas] = useState<Cinema[]>([]);
  const [selectedCinemaId, setSelectedCinemaId] = useState<number | null>(null);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [loadingCinemas, setLoadingCinemas] = useState(true);
  const [loadingShowtimes, setLoadingShowtimes] = useState(false);

  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');

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



  // Cache tên phim động theo movie_id (fetch từng cái nếu chưa có)
  const [movieMap, setMovieMap] = useState<{ [id: string]: string }>({});
  useEffect(() => {
    // Lấy tất cả movie_id chưa có tên
    const missingIds = Array.from(new Set(showtimes.map(st => String(st.movie_id)))).filter(id => !movieMap[id]);
    if (missingIds.length === 0) return;
    missingIds.forEach(id => {
      fetch(`https://movies.cegove.cloud/api/v1/movies/${id}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data && data.series_title) {
            setMovieMap(prev => ({ ...prev, [id]: data.series_title }));
          }
        });
    });
  }, [showtimes]);

  useEffect(() => {
    async function loadShowtimes() {
      if (!selectedCinemaId) {
        setShowtimes([]);
        return;
      }
      setLoadingShowtimes(true);
      try {
        const res = await fetch(`https://booking.cegove.cloud/api/v1/showtimes?cinema_id=${selectedCinemaId}`);
        const data = await res.json();
        setShowtimes(Array.isArray(data) ? data : []);
      } catch (e) {
        setShowtimes([]);
      } finally {
        setLoadingShowtimes(false);
      }
    }
    loadShowtimes();
  }, [selectedCinemaId]);

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>Quản lý lịch chiếu</h1>
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
      </div>
      {loadingCinemas ? (
        <div>Đang tải danh sách rạp...</div>
      ) : loadingShowtimes ? (
        <div>Đang tải lịch chiếu...</div>
      ) : (
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ textAlign: 'center' }}>ID</th>
                <th style={{ textAlign: 'center' }}>Tên phim</th>
                <th style={{ textAlign: 'center' }}>Thời gian bắt đầu</th>
                <th style={{ textAlign: 'center' }}>Thời gian kết thúc</th>
                <th style={{ textAlign: 'center' }}>Giá vé</th>
              </tr>
            </thead>
            <tbody>
              {selectedCinemaId == null ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#888' }}>Vui lòng chọn rạp</td></tr>
              ) : showtimes.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#888' }}>Không có lịch chiếu nào</td></tr>
              ) : (
                showtimes.map(st => (
                  <tr key={st.id}>
                    <td style={{ textAlign: 'center' }}>{st.id}</td>
                    <td style={{ textAlign: 'center' }}>{movieMap[String(st.movie_id)] ?? st.movie_id}</td>
                    <td style={{ textAlign: 'center' }}>{new Date(st.start_time).toLocaleString()}</td>
                    <td style={{ textAlign: 'center' }}>{new Date(st.end_time).toLocaleString()}</td>
                    <td style={{ textAlign: 'center' }}>{st.base_price.toLocaleString()} đ</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
