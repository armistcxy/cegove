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
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedYear, setSelectedYear] = useState('');

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
      
      // Add search parameter if searchTerm exists
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
  const genres = [...new Set(movies.map(m => m.genre).filter(g => g))].sort();
  const years = [...new Set(movies.map(m => m.released_year).filter(y => y))].sort().reverse();

  // Filter movies based on genre and year only (search is handled by API)
  const filteredMovies = movies.filter(movie => {
    const matchesGenre = !selectedGenre || movie.genre === selectedGenre;
    const matchesYear = !selectedYear || movie.released_year === selectedYear;
    return matchesGenre && matchesYear;
  });

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Quản lý Phim</h1>
        <button className={styles.btnPrimary}>+ Thêm phim mới</button>
      </div>

      {/* Filter Section */}
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
        <select
          value={selectedGenre}
          onChange={(e) => setSelectedGenre(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">Tất cả thể loại</option>
          {genres.map(genre => (
            <option key={genre} value={genre}>{genre}</option>
          ))}
        </select>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">Tất cả năm</option>
          {years.map(year => (
            <option key={year} value={year}>{year}</option>
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
                            className={styles.btnEdit}
                            onClick={() => handleEdit(movie.id)}
                          >
                            ✏️
                          </button>
                          <button 
                            className={styles.btnDelete}
                            onClick={() => handleDelete(movie.id)}
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
