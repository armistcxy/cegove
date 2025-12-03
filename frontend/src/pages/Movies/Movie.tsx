import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { Movie, MoviesResponse } from "./MovieLogic.ts";
import { fetchMovies } from "./MovieLogic.ts";
import styles from "./Movie.module.css";

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMorePages, setHasMorePages] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadedMovieIds, setLoadedMovieIds] = useState<Set<number>>(new Set());
  const navigate = useNavigate();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadingRef = useRef<HTMLDivElement | null>(null);
  const isLoadingRef = useRef(false);

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
      const response: MoviesResponse = await fetchMovies(page, 24);
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
  }, []);

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


  useEffect(() => {
    loadMovies(1, true);
  }, []); 

  const handleDetailClick = (movieId: number) => {
    navigate(`/MovieDetail/${movieId}`);
  };

  const handleBuyClick = () => {
    navigate('/NotAvailable');
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
      <h2>Phim Đang Chiếu</h2>
      
      <div className={styles.moviesGrid}>
        {movies.map((m, index) => (
          <div className={styles.movieCard} key={`${m.id}-${index}`}>
            <img src={m.poster_link} alt={m.series_title} className={styles.poster} />
            <div className={styles.movieInfo}>
              <p className={styles.movieTitle}>{m.series_title}</p>
              <div className={styles.movieButtons}>
                <button 
                  className={styles.btnBuy}
                  onClick={handleBuyClick}
                >
                  Buy
                </button>
                <button 
                  className={styles.btnDetail}
                  onClick={() => handleDetailClick(m.id)}
                >
                  Detail
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
    </div>
  );
}
