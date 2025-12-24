import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCinemas, fetchCities } from './CinemaLogic';
import styles from './Cinema.module.css';

interface Cinema {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
  email: string;
}

export default function Cinema() {
  const navigate = useNavigate();
  const [allCinemas, setAllCinemas] = useState<Cinema[]>([]);
  const [filteredCinemas, setFilteredCinemas] = useState<Cinema[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadAllCinemas();
  }, []);

  useEffect(() => {
    filterCinemas();
  }, [selectedCity, allCinemas]);

  const loadAllCinemas = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchCinemas();
      setAllCinemas(data);
      
      // Extract unique cities
      const uniqueCities = [...new Set(data.map(cinema => cinema.city))];
      setCities(uniqueCities.sort());
    } catch (err) {
      setError('Không thể tải danh sách rạp. Vui lòng thử lại sau.');
      console.error('Error loading cinemas:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterCinemas = () => {
    if (!selectedCity) {
      setFilteredCinemas(allCinemas);
    } else {
      const filtered = allCinemas.filter(cinema => cinema.city === selectedCity);
      setFilteredCinemas(filtered);
    }
  };

  const handleCityChange = (city: string) => {
    setSelectedCity(city);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Hệ Thống Rạp CGV</h1>
        <p>Khám phá các rạp chiếu phim CGV trên toàn quốc</p>
      </div>

      {/* Filter */}
      <div
        className={styles.filterSection}
        style={{
          border: '2px solid #f4433633', // viền đỏ dày như thẻ rạp
          borderRadius: 12,
          padding: 16,
          marginBottom: 24,
          background: '#fff',
        }}
      >
        <div className={styles.filterGroup}>
          <label>Chọn thành phố:</label>
          <select 
            value={selectedCity} 
            onChange={(e) => handleCityChange(e.target.value)}
            className={styles.select}
          >
            <option value="">Tất cả thành phố</option>
            {cities.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Đang tải danh sách rạp...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className={styles.error}>
          {error}
        </div>
      )}

      {/* Cinema Grid */}
      {!loading && !error && (
        <div className={styles.cinemaGrid}>
          {filteredCinemas.length === 0 ? (
            <div className={styles.noResults}>
              Không tìm thấy rạp phim nào.
            </div>
          ) : (
            filteredCinemas.map((cinema) => (
              <div
                key={cinema.id}
                className={styles.cinemaCard}
                style={{
                  border: '2px solid #f4433633', // viền đỏ dày hơn
                  boxShadow: '0 2px 8px 0 rgba(183,28,28,0.04)', // bóng nhẹ
                  borderRadius: 12,
                }}
              >
                <div className={styles.cinemaHeader}>
                  <h3>{cinema.name}</h3>
                  <span className={styles.cityBadge}>{cinema.city}</span>
                </div>
                <div className={styles.cinemaInfo}>
                  <div className={styles.infoRow}>
                    <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <div>
                      <p className={styles.address}>{cinema.address}</p>
                      <p className={styles.district}>{cinema.district}</p>
                    </div>
                  </div>
                  <div className={styles.infoRow}>
                    <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <p>{cinema.phone}</p>
                  </div>
                  <div className={styles.infoRow}>
                    <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <p>{cinema.email}</p>
                  </div>
                </div>
                <button
                  className={styles.detailBtn}
                  onClick={() => navigate(`/CinemaDetails/${cinema.id}`)}
                >
                  Xem chi tiết
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
