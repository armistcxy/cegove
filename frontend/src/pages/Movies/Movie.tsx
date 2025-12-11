import { useEffect, useState, useRef, useCallback } from "react";
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
  const [hasMorePages, setHasMorePages] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadedMovieIds, setLoadedMovieIds] = useState<Set<number>>(new Set());
  
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
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadingRef = useRef<HTMLDivElement | null>(null);
  const isLoadingRef = useRef(false);

  const getActiveFilters = useCallback((): MovieFilters => {
    const filters: MovieFilters = {};
    if (appliedGenre) filters.genre = appliedGenre;
    filters.min_rating = appliedMinRating;
    if (appliedSortBy) filters.sort_by = appliedSortBy;
    return filters;
  }, [appliedGenre, appliedMinRating, appliedSortBy]);

  const loadMovies = useCallback(async (page: number, isInitial: boolean = false) => {
    // Prevent multiple simultaneous requests
    if (isLoadingRef.current) {
      console.log('Request blocked - already loading');
      return;
    }
    
    console.log('Loading movies for page:', page, 'isInitial:', isInitial);
    
    isLoadingRef.current = true;
    setLoading(true);
    setError(null);
    
    try {
      const filters = getActiveFilters();
      const response: MoviesResponse = await fetchMovies(page, 24, filters);
      console.log('Fetched movies:', response.items.length, 'total_pages:', response.total_pages);
      
      if (isInitial) {
        setMovies(response.items);
        setLoadedMovieIds(new Set(response.items.map(movie => movie.id)));
        setInitialLoading(false);
      } else {
        setMovies(prev => {
          const existingIds = new Set(prev.map(movie => movie.id));
          const newMovies = response.items.filter(movie => !existingIds.has(movie.id));
          console.log('Adding new movies:', newMovies.length, 'total movies will be:', prev.length + newMovies.length);
          return [...prev, ...newMovies];
        });
        
        setLoadedMovieIds(prev => {
          const newSet = new Set(prev);
          response.items.forEach(movie => newSet.add(movie.id));
          return newSet;
        });
      }
      
      setCurrentPage(page);
      const hasMore = page < response.total_pages;
      setHasMorePages(hasMore);
      console.log('Updated state - currentPage:', page, 'hasMorePages:', hasMore);
    } catch (err) {
      console.error('Error loading movies:', err);
      setError("Failed to load movies. Please try again.");
      if (isInitial) {
        setInitialLoading(false);
      }
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
      console.log('Loading completed');
    }
  }, [getActiveFilters]);

  const loadMoreMovies = useCallback(() => {
    if (!isLoadingRef.current && hasMorePages && !loading) {
      console.log('Loading more movies, current page:', currentPage);
      loadMovies(currentPage + 1);
    }
  }, [currentPage, hasMorePages, loading, loadMovies]);

  useEffect(() => {
    if (!loadingRef.current || !hasMorePages || loading) return;

    console.log('Setting up intersection observer, hasMorePages:', hasMorePages);

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        console.log('Intersection observed:', entry.isIntersecting, 'hasMorePages:', hasMorePages, 'loading:', isLoadingRef.current);
        
        if (entry.isIntersecting && hasMorePages && !isLoadingRef.current) {
          console.log('Triggering load more movies');
          loadMoreMovies();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '100px'
      }
    );

    observer.observe(loadingRef.current);
    observerRef.current = observer;

    return () => {
      console.log('Cleaning up intersection observer');
      observer.disconnect();
    };
  }, [loadMoreMovies, hasMorePages, loading]);

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
      setLoadedMovieIds(new Set());
      setCurrentPage(1);
      setHasMorePages(true);
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
    if (movies.length === 0) {
      setInitialLoading(true);
      setCurrentPage(1);
      setHasMorePages(true);
      setLoadedMovieIds(new Set());
      loadMovies(1, true);
    } else {
      loadMovies(currentPage + 1);
    }
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
      {hasMorePages && (
        <div ref={loadingRef} className={styles.loadMoreContainer}>
          {loading ? (
            <div className={styles.loadingMore}>
              <div className={styles.spinner}></div>
              <p>Đang tải thêm phim...</p>
            </div>
          ) : (
            <div className={styles.loadMoreTrigger}>
              <p>Kéo xuống để xem thêm phim</p>
            </div>
          )}
        </div>
      )}
      
      {/* End of content indicator */}
      {!hasMorePages && movies.length > 0 && (
        <div className={styles.endOfContent}>
          <p>🎬 Bạn đã xem hết tất cả phim có sẵn! 🎬</p>
        </div>
      )}
      
      {/* Error state for loading more */}
      {error && movies.length > 0 && (
        <div className={styles.loadMoreError}>
          <p className={styles.errorMessage}>{error}</p>
          <button className={styles.retryButton} onClick={handleRetry}>
            Thử lại
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
