import { useEffect, useState } from "react";
import type { Movie } from "../Movies/MovieLogic";
import { fetchRecentMovies } from "./RecentMovieLogic";
import BookingPopup from "../../components/BookingPopup/BookingPopup.tsx";
import styles from "../Movies/Movie.module.css";

export default function RecentMovie() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  const [selectedMovieTitle, setSelectedMovieTitle] = useState<string>("");
  const [selectedMovieId, setSelectedMovieId] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetchRecentMovies()
      .then(setMovies)
      .catch(() => setError("Không thể tải phim đang chiếu."))
      .finally(() => setLoading(false));
  }, []);

  const handleDetailClick = (movieId: number) => {
    window.location.href = `/MovieDetail/${movieId}`;
  };

  const handleBuyClick = (movieTitle: string, movieId: number) => {
    setSelectedMovieTitle(movieTitle);
    setSelectedMovieId(movieId);
    setIsBookingOpen(true);
  };

  if (loading) {
    return (
      <div className={styles.moviesSection}>
        <div className={styles.header}>
          <h2>Phim Đang Chiếu</h2>
        </div>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải phim...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.moviesSection}>
        <div className={styles.header}>
          <h2>Phim Đang Chiếu</h2>
        </div>
        <div className={styles.errorContainer}>
          <p className={styles.errorMessage}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.moviesSection}>
      <div className={styles.header}>
        <h2>Phim Đang Chiếu</h2>
      </div>
      <div className={styles.moviesGrid}>
        {movies.length === 0 ? (
          <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '2rem', color: '#888' }}>
            Không tìm thấy phim nào.
          </div>
        ) : (
          movies.map((m, index) => (
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
          ))
        )}
      </div>
      <BookingPopup 
        isOpen={isBookingOpen}
        onClose={() => setIsBookingOpen(false)}
        movieTitle={selectedMovieTitle}
        movieId={selectedMovieId}
      />
    </div>
  );
}
