import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Movie } from "../../pages/Movies/MovieLogic";
import { fetchMovies } from "../../pages/Movies/MovieLogic";
import styles from "./MovieGrid.module.css";

interface MovieGridProps {
  title?: string;
  limit?: number;
  showTitle?: boolean;
  gridColumns?: number;
}

export default function MovieGrid({ 
  title = "Phim Đang Chiếu", 
  limit = 8,
  showTitle = true,
  gridColumns = 4 
}: MovieGridProps) {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadMovies = async () => {
      try {
        setLoading(true);
        const response = await fetchMovies(1, limit);
        setMovies(response.items);
      } catch (err) {
        console.error('Error loading movies:', err);
        setError("Failed to load movies. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    loadMovies();
  }, [limit]);

  const handleDetailClick = (movieId: number) => {
    navigate(`/MovieDetail/${movieId}`);
  };

  const handleBuyClick = () => {
    navigate('/NotAvailable');
  };

  if (loading) {
    return (
      <div className={styles.movieSection}>
        {showTitle && <h2>{title}</h2>}
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải phim...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.movieSection}>
        {showTitle && <h2>{title}</h2>}
        <div className={styles.errorContainer}>
          <p className={styles.errorMessage}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.movieSection}>
      {showTitle && <h2>{title}</h2>}
      
      <div 
        className={styles.moviesGrid}
        style={{ gridTemplateColumns: `repeat(${gridColumns}, 1fr)` }}
      >
        {movies.map((movie) => (
          <div className={styles.movieCard} key={movie.id}>
            <img 
              src={movie.poster_link} 
              alt={movie.series_title} 
              className={styles.poster} 
            />
            <div className={styles.movieInfo}>
              <p className={styles.movieTitle}>{movie.series_title}</p>
              <div className={styles.movieButtons}>
                <button 
                  className={styles.btnBuy}
                  onClick={handleBuyClick}
                >
                  Mua vé
                </button>
                <button 
                  className={styles.btnDetail}
                  onClick={() => handleDetailClick(movie.id)}
                >
                  Xem chi tiết
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}