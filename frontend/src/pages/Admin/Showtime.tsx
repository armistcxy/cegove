import React, { useEffect, useState } from 'react';
// Monochromos loading spinner
function MonochromosLoader() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 120 }}>
      <div style={{
        width: 48,
        height: 48,
        border: '6px solid #bbb',
        borderTop: '6px solid #222',
        borderRadius: '50%',
        animation: 'mono-spin 1s linear infinite',
      }} />
      <style>{`
        @keyframes mono-spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
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
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
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



  // Cache tên phim động theo movie_id (fetch tất cả cùng lúc khi lấy showtimes)
  const [movieMap, setMovieMap] = useState<{ [id: string]: string }>({});

  useEffect(() => {
    async function loadShowtimes() {
      if (!selectedCinemaId) {
        setShowtimes([]);
        setMovieMap({});
        return;
      }
      setLoadingShowtimes(true);
      try {
        const res = await fetch(`https://booking.cegove.cloud/api/v1/showtimes?cinema_id=${selectedCinemaId}`);
        const data = await res.json();
        // Sort by start_time ascending
        const sorted = Array.isArray(data)
          ? [...data].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
          : [];
        setShowtimes(sorted);
        // Chỉ fetch tên phim cho trang 1 trước
        const idsPage1 = sorted.slice(0, pageSize).map(st => String(st.movie_id));
        const uniqueIdsPage1 = Array.from(new Set(idsPage1));
        const movieFetches = uniqueIdsPage1.map(id =>
          fetch(`https://movies.cegove.cloud/api/v1/movies/${id}`)
            .then(res => res.ok ? res.json() : null)
            .then(data => ({ id, title: data && data.series_title ? data.series_title : id }))
        );
        const movieResults = await Promise.all(movieFetches);
        const movieMapObj: { [id: string]: string } = {};
        movieResults.forEach(({ id, title }) => { movieMapObj[id] = title; });
        setMovieMap(movieMapObj);
        // Sau khi render trang đầu, fetch tên phim cho các trang sau (nếu có)
        setTimeout(() => {
          const idsRest = sorted.slice(pageSize).map(st => String(st.movie_id)).filter(id => !(id in movieMapObj));
          const uniqueIdsRest = Array.from(new Set(idsRest));
          if (uniqueIdsRest.length > 0) {
            Promise.all(uniqueIdsRest.map(id =>
              fetch(`https://movies.cegove.cloud/api/v1/movies/${id}`)
                .then(res => res.ok ? res.json() : null)
                .then(data => ({ id, title: data && data.series_title ? data.series_title : id }))
            )).then(restResults => {
              setMovieMap(prev => {
                const next = { ...prev };
                restResults.forEach(({ id, title }) => { next[id] = title; });
                return next;
              });
            });
          }
        }, 0);
      } catch (e) {
        setShowtimes([]);
        setMovieMap({});
      } finally {
        setLoadingShowtimes(false);
      }
    }
    loadShowtimes();
  }, [selectedCinemaId]);

  // Pagination logic
  const totalPages = Math.ceil(showtimes.length / pageSize);
  const paginatedShowtimes = showtimes.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>Quản lý lịch chiếu</h1>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16, justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <label htmlFor="city-select" style={{ fontWeight: 500 }}>Chọn thành phố:</label>
          <select
            id="city-select"
            value={selectedCity}
            onChange={e => { setSelectedCity(e.target.value); setCurrentPage(1); }}
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
            onChange={e => { setSelectedCinemaId(e.target.value ? Number(e.target.value) : null); setCurrentPage(1); }}
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
        <MonochromosLoader />
      ) : loadingShowtimes ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <MonochromosLoader />
          <div style={{ color: '#555', marginTop: 8, fontSize: 16 }}>Đang tải showtime...</div>
        </div>
      ) : (
        <>
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
                  paginatedShowtimes.map(st => (
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
          {/* Pagination controls */}
          {showtimes.length > pageSize && (
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16, gap: 8 }}>
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{ padding: '6px 12px', borderRadius: 4, border: '1px solid #bbb', background: currentPage === 1 ? '#eee' : '#fff', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
              >
                Trước
              </button>
              <span style={{ alignSelf: 'center' }}>Trang {currentPage} / {totalPages}</span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{ padding: '6px 12px', borderRadius: 4, border: '1px solid #bbb', background: currentPage === totalPages ? '#eee' : '#fff', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
              >
                Sau
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
