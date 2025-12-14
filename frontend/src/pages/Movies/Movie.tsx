import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { Movie, MoviesResponse, MovieFilters } from "./MovieLogic.ts";
import { fetchMovies, fetchGenres } from "./MovieLogic.ts";
import BookingPopup from "../../components/BookingPopup/BookingPopup.tsx";
import styles from "./Movie.module.css";

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [initialLoading, setInitialLoading] = useState(true);
  
  // Filter states
  const [genres, setGenres] = useState<string[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string>("");
  const [minRating, setMinRating] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'votes_asc' | 'votes_desc' | ''>("");
  const [showFilters, setShowFilters] = useState(false);
  
  // Applied filters (only updated when user clicks Apply)
  const [appliedGenre, setAppliedGenre] = useState<string>("");
  const [appliedMinRating, setAppliedMinRating] = useState<number>(0);
  const [appliedSortBy, setAppliedSortBy] = useState<'votes_asc' | 'votes_desc' | ''>("");
  const [filterTrigger, setFilterTrigger] = useState<number>(0);
  
  // Booking popup state
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  const [selectedMovieTitle, setSelectedMovieTitle] = useState<string>("");
  const [selectedMovieId, setSelectedMovieId] = useState<number | undefined>(undefined);
  
  const navigate = useNavigate();


  const getActiveFilters = useCallback((): MovieFilters => {
    const filters: MovieFilters = {};
    if (appliedGenre) filters.genre = appliedGenre;
    filters.min_rating = appliedMinRating;
    if (appliedSortBy) filters.sort_by = appliedSortBy;
    return filters;
  }, [appliedGenre, appliedMinRating, appliedSortBy]);

  const loadMovies = useCallback(async (page: number, isInitial: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      const filters = getActiveFilters();
      const response: MoviesResponse = await fetchMovies(page, 24, filters);
      setMovies(response.items);
      setCurrentPage(page);
      setTotalPages(response.total_pages);
      if (isInitial) setInitialLoading(false);
    } catch (err) {
      setError("Failed to load movies. Please try again.");
      if (isInitial) setInitialLoading(false);
    } finally {
      setLoading(false);
    }
  }, [getActiveFilters]);





  // Load genres on component mount
  useEffect(() => {
    const loadGenres = async () => {
      const genreList = await fetchGenres();
      setGenres(genreList);
    };
    loadGenres();
  }, []);

  // Initial load
  useEffect(() => {
    loadMovies(1, true);
  }, []);

  // Reload movies when filters change
  useEffect(() => {
    if (filterTrigger > 0) {
      setMovies([]);
      setCurrentPage(1);
      setTotalPages(1);
      setInitialLoading(true);
      loadMovies(1, true);
    }
  }, [filterTrigger]);

  const handleApplyFilters = () => {
    // Apply the selected filters
    setAppliedGenre(selectedGenre);
    setAppliedMinRating(minRating);
    setAppliedSortBy(sortBy);
    setFilterTrigger(prev => prev + 1); // Trigger reload
    setShowFilters(false);
  };

  const handleResetFilters = () => {
    setSelectedGenre("");
    setMinRating(0);
    setSortBy("");
    setAppliedGenre("");
    setAppliedMinRating(0);
    setAppliedSortBy("");
  };

  const handleDetailClick = (movieId: number) => {
    navigate(`/MovieDetail/${movieId}`);
  };

  const handleBuyClick = (movieTitle: string, movieId: number) => {
    setSelectedMovieTitle(movieTitle);
    setSelectedMovieId(movieId);
    setIsBookingOpen(true);
  };

  const handleRetry = () => {
    setError(null);
    setInitialLoading(true);
    setCurrentPage(1);
    setTotalPages(1);
    loadMovies(1, true);
  };

  const hasActiveFilters = appliedGenre || appliedMinRating > 0 || appliedSortBy;

  if (initialLoading) {
    return (
      <div className={styles.moviesSection}>
        <h2>Phim Đang Chiếu</h2>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải phim...</p>
        </div>
      </div>
    );
  }

  if (error && movies.length === 0) {
    return (
      <div className={styles.moviesSection}>
        <h2>Phim Đang Chiếu</h2>
        <div className={styles.errorContainer}>
          <p className={styles.errorMessage}>{error}</p>
          <button className={styles.retryButton} onClick={handleRetry}>
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.moviesSection}>
      <div className={styles.header}>
        <h2>Phim Đang Chiếu</h2>
        <button 
          className={styles.filterToggle}
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? '✕ Đóng bộ lọc' : ' Bộ lọc'} 
          {hasActiveFilters && <span className={styles.filterBadge}>● </span>}
        </button>
      </div>

      {showFilters && (
        <div className={styles.filterPanel}>
          <div className={styles.filterGroup}>
            <label htmlFor="genre">Thể loại:</label>
            <select 
              id="genre"
              value={selectedGenre} 
              onChange={(e) => setSelectedGenre(e.target.value)}
              className={styles.filterSelect}
            >
              <option value="">Tất cả thể loại</option>
              {genres.map((genre) => (
                <option key={genre} value={genre}>
                  {genre}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label htmlFor="minRating">Điểm IMDb tối thiểu:</label>
            <input
              id="minRating"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={minRating}
              onChange={(e) => setMinRating(e.target.value ? parseFloat(e.target.value) : 0)}
              placeholder="0.0"
              className={styles.filterInput}
            />
          </div>

          <div className={styles.filterGroup}>
            <label htmlFor="sortBy">Sắp xếp theo độ phổ biến:</label>
            <select 
              id="sortBy"
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as 'votes_asc' | 'votes_desc' | '')}
              className={styles.filterSelect}
            >
              <option value="">Mặc định</option>
              <option value="votes_desc">Phổ biến nhất (giảm dần)</option>
              <option value="votes_asc">Ít phổ biến nhất (tăng dần)</option>
            </select>
          </div>

          <div className={styles.filterActions}>
            <button 
              className={styles.btnReset}
              onClick={handleResetFilters}
              disabled={!hasActiveFilters}
            >
              Đặt lại
            </button>
            <button 
              className={styles.btnApply}
              onClick={handleApplyFilters}
            >
              Áp dụng
            </button>
          </div>
        </div>
      )}

      {hasActiveFilters && (
        <div className={styles.activeFilters}>
          <span>Bộ lọc đang áp dụng:</span>
          {appliedGenre && <span className={styles.filterTag}>Thể loại: {appliedGenre}</span>}
          {appliedMinRating > 0 && <span className={styles.filterTag}>IMDb ≥ {appliedMinRating}</span>}
          {appliedSortBy && (
            <span className={styles.filterTag}>
              {appliedSortBy === 'votes_desc' ? 'Phổ biến nhất' : 'Ít phổ biến nhất'}
            </span>
          )}
        </div>
      )}
      
      <div className={styles.moviesGrid}>
        {movies.map((m, index) => (
          <div className={styles.movieCard} key={`${m.id}-${index}`}>
            <img src={m.poster_link} alt={m.series_title} className={styles.poster} />
            <div className={styles.movieInfo}>
              <p className={styles.movieTitle}>{m.series_title}</p>
              <div className={styles.movieButtons}>
                <button 
                  className={styles.btnBuy}
                  onClick={() => handleBuyClick(m.series_title, m.id)}
                >
                  Mua vé
                </button>
                <button 
                  className={styles.btnDetail}
                  onClick={() => handleDetailClick(m.id)}
                >
                  Xem chi tiết
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Loading indicator for infinite scroll */}
      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className={styles.paginationContainer}>
          <button
            className={styles.paginationButton}
            onClick={() => loadMovies(currentPage - 1)}
            disabled={currentPage === 1 || loading}
          >
            &lt; Trước
          </button>
          {/* Pagination numbers with ellipsis */}
          {(() => {
            const pageButtons = [];
            const pageWindow = 2; // show 2 pages before/after current
            const showFirst = 1;
            const showLast = totalPages;
            let left = Math.max(currentPage - pageWindow, 2);
            let right = Math.min(currentPage + pageWindow, totalPages - 1);

            // Always show first page
            pageButtons.push(
              <button
                key={1}
                className={currentPage === 1 ? styles.paginationButtonActive : styles.paginationButton}
                onClick={() => loadMovies(1)}
                disabled={currentPage === 1 || loading}
              >
                1
              </button>
            );

            // Ellipsis if needed
            if (left > 2) {
              pageButtons.push(<span key="start-ellipsis">...</span>);
            }

            // Page window
            for (let i = left; i <= right; i++) {
              pageButtons.push(
                <button
                  key={i}
                  className={currentPage === i ? styles.paginationButtonActive : styles.paginationButton}
                  onClick={() => loadMovies(i)}
                  disabled={currentPage === i || loading}
                >
                  {i}
                </button>
              );
            }

            // Ellipsis if needed
            if (right < totalPages - 1) {
              pageButtons.push(<span key="end-ellipsis">...</span>);
            }

            // Always show last page if more than 1
            if (totalPages > 1) {
              pageButtons.push(
                <button
                  key={totalPages}
                  className={currentPage === totalPages ? styles.paginationButtonActive : styles.paginationButton}
                  onClick={() => loadMovies(totalPages)}
                  disabled={currentPage === totalPages || loading}
                >
                  {totalPages}
                </button>
              );
            }
            return pageButtons;
          })()}
          <button
            className={styles.paginationButton}
            onClick={() => loadMovies(currentPage + 1)}
            disabled={currentPage === totalPages || loading}
          >
            Sau &gt;
          </button>
        </div>
      )}
      
      {/* Booking Popup */}
      <BookingPopup 
        isOpen={isBookingOpen}
        onClose={() => setIsBookingOpen(false)}
        movieTitle={selectedMovieTitle}
        movieId={selectedMovieId}
      />
    </div>
  );
}
