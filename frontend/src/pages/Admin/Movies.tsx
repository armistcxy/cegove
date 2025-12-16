import { useEffect, useState } from 'react';
import styles from './Admin.module.css';

interface Movie {
  id: number;
  series_title: string;
  poster_link: string;
  released_year: string;
  genre: string;
}

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  // Đã bỏ filter thể loại và năm

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchMovies();
    }, 500); // Debounce 500ms

    return () => clearTimeout(delayDebounceFn);
  }, [currentPage, searchTerm]);
  const fetchMovies = async () => {
    setLoading(true);
    try {
      let url = `https://movies.cegove.cloud/api/v1/movies/?page=${currentPage}&page_size=20&sort_order=desc`;
      if (searchTerm.trim()) {
        url += `&search=${encodeURIComponent(searchTerm)}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setMovies(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Bạn có chắc chắn muốn xóa phim này?')) {
      // TODO: Implement delete API
      console.log('Delete movie:', id);
    }
  };

  const handleEdit = (id: number) => {
    // TODO: Implement edit functionality
    console.log('Edit movie:', id);
  };

  // Get unique genres and years for filters (client-side only)
  // Bỏ filter thể loại và năm
  const filteredMovies = movies;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Quản lý Phim</h1>
        <button className={styles.btnPrimary}>+ Thêm phim mới</button>
      </div>

      {/* Filter Section chỉ còn search */}
      <div className={styles.filterSection}>
        <input
          type="text"
          placeholder="Tìm kiếm theo tên phim (search toàn bộ database)..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1); // Reset to first page on new search
          }}
          className={styles.searchInput}
        />
      </div>

      {loading ? (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : (
        <>
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Poster</th>
                  <th>Title</th>
                  <th>Release Year</th>
                  <th>Genres</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredMovies.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.noData}>
                      Không tìm thấy phim nào
                    </td>
                  </tr>
                ) : (
                  filteredMovies.map((movie) => (
                    <tr key={movie.id}>
                      <td>{movie.id}</td>
                      <td>
                        <img 
                          src={movie.poster_link} 
                          alt={movie.series_title}
                          className={styles.posterThumb}
                        />
                      </td>
                      <td className={styles.movieTitle}>{movie.series_title}</td>
                      <td>{movie.released_year}</td>
                      <td>
                        <span className={styles.genreTag}>{movie.genre}</span>
                      </td>
                      <td>
                        <span className={styles.statusActive}>Active</span>
                      </td>
                      <td>
                        <div className={styles.actionButtons}>
                          <button
                            style={{
                              marginRight: 8,
                              padding: '6px 14px',
                              borderRadius: 6,
                              border: '1px solid #bbb',
                              background: '#fff',
                              color: '#222',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'background 0.2s, color 0.2s',
                            }}
                            onMouseOver={e => {
                              e.currentTarget.style.background = '#222';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={e => {
                              e.currentTarget.style.background = '#fff';
                              e.currentTarget.style.color = '#222';
                            }}
                            onClick={() => handleEdit(movie.id)}
                            title="Chỉnh sửa"
                          >
                            Sửa
                          </button>
                          <button
                            style={{
                              padding: '6px 14px',
                              borderRadius: 6,
                              border: '1px solid #bbb',
                              background: '#fff',
                              color: '#222',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'background 0.2s, color 0.2s',
                            }}
                            onMouseOver={e => {
                              e.currentTarget.style.background = '#222';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={e => {
                              e.currentTarget.style.background = '#fff';
                              e.currentTarget.style.color = '#222';
                            }}
                            onClick={() => handleDelete(movie.id)}
                            title="Xóa"
                          >
                            Xóa
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.pagination}>
            <button 
              className={styles.paginationBtn}
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              ← Previous
            </button>
            <span className={styles.pageInfo}>
              Page {currentPage} of {totalPages}
            </span>
            <button 
              className={styles.paginationBtn}
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
