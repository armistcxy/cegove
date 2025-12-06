import { useEffect, useState } from 'react';
import { fetchCinemas } from '../Cinemas/CinemaLogic';
import styles from './Admin.module.css';

interface Cinema {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
  email: string;
}

export default function Cinemas() {
  const [cinemas, setCinemas] = useState<Cinema[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('');

  useEffect(() => {
    loadCinemas();
  }, []);

  const loadCinemas = async () => {
    setLoading(true);
    try {
      const data = await fetchCinemas();
      setCinemas(data);
    } catch (error) {
      console.error('Error loading cinemas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Bạn có chắc chắn muốn xóa rạp này?')) {
      // TODO: Implement delete API
      console.log('Delete cinema:', id);
    }
  };

  const handleEdit = (id: number) => {
    // TODO: Implement edit functionality
    console.log('Edit cinema:', id);
  };

  // Get unique cities for filter
  const cities = [...new Set(cinemas.map(c => c.city))].sort();

  // Filter cinemas based on search and city
  const filteredCinemas = cinemas.filter(cinema => {
    const matchesSearch = cinema.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         cinema.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCity = !selectedCity || cinema.city === selectedCity;
    return matchesSearch && matchesCity;
  });

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Quản lý Rạp Chiếu Phim</h1>
        <button className={styles.btnPrimary}>+ Thêm rạp mới</button>
      </div>

      {/* Filter Section */}
      <div className={styles.filterSection}>
        <input
          type="text"
          placeholder="Tìm kiếm theo tên rạp hoặc địa chỉ..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className={styles.searchInput}
        />
        <select
          value={selectedCity}
          onChange={(e) => setSelectedCity(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">Tất cả thành phố</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : (
        <>
          <div className={styles.statsCard}>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Tổng số rạp:</span>
              <span className={styles.statValue}>{cinemas.length}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Kết quả hiển thị:</span>
              <span className={styles.statValue}>{filteredCinemas.length}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Số thành phố:</span>
              <span className={styles.statValue}>{cities.length}</span>
            </div>
          </div>

          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Tên rạp</th>
                  <th>Thành phố</th>
                  <th>Quận/Huyện</th>
                  <th>Địa chỉ</th>
                  <th>Số điện thoại</th>
                  <th>Email</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredCinemas.length === 0 ? (
                  <tr>
                    <td colSpan={8} className={styles.noData}>
                      Không tìm thấy rạp chiếu phim nào
                    </td>
                  </tr>
                ) : (
                  filteredCinemas.map((cinema) => (
                    <tr key={cinema.id}>
                      <td>{cinema.id}</td>
                      <td className={styles.cinemaName}>{cinema.name}</td>
                      <td>
                        <span className={styles.cityTag}>{cinema.city}</span>
                      </td>
                      <td>{cinema.district}</td>
                      <td className={styles.addressCell}>{cinema.address}</td>
                      <td>{cinema.phone}</td>
                      <td className={styles.emailCell}>{cinema.email}</td>
                      <td>
                        <div className={styles.actionButtons}>
                          <button 
                            className={styles.btnEdit}
                            onClick={() => handleEdit(cinema.id)}
                            title="Chỉnh sửa"
                          >
                            ✏️
                          </button>
                          <button 
                            className={styles.btnDelete}
                            onClick={() => handleDelete(cinema.id)}
                            title="Xóa"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
