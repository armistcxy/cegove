import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../../context/UserContext.tsx";
import type { Movie } from "../Movies/MovieLogic.ts";
import { fetchPersonalizedMovies } from "./MoviesForYouLogic.ts";
import BookingPopup from "../../components/BookingPopup/BookingPopup.tsx";
import styles from "./MoviesForYou.module.css";

export default function MoviesForYou() {
  const { isLoggedIn, userProfile } = useUser();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Booking popup state
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  const [selectedMovieTitle, setSelectedMovieTitle] = useState<string>("");
  const [selectedMovieId, setSelectedMovieId] = useState<number | undefined>(undefined);
  
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    const loadPersonalizedMovies = async () => {
      setLoading(true);
      setError(null);

      try {
        const userId = userProfile.id || 0;
        const response = await fetchPersonalizedMovies(userId, 20, 0.7, true);

        if (response && response.recommendations) {
          setMovies(response.recommendations);
        } else {
          setError("Không thể tải danh sách phim đề xuất");
        }
      } catch (err) {
        console.error("Error loading personalized movies:", err);
        setError("Đã xảy ra lỗi khi tải danh sách phim");
      } finally {
        setLoading(false);
      }
    };

    loadPersonalizedMovies();
  }, [isLoggedIn, userProfile.id, navigate]);

  const handleBuyClick = (movieTitle: string, movieId: number) => {
    setSelectedMovieTitle(movieTitle);
    setSelectedMovieId(movieId);
    setIsBookingOpen(true);
  };

  const handleDetailClick = (movieId: number) => {
    navigate(`/MovieDetail/${movieId}`);
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Đang tải phim dành cho bạn...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Lỗi</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.moviesSection}>
      <div className={styles.header}>
        <div>
          <h2>Phim dành cho bạn</h2>
          <p className={styles.subtitle}>
            {movies.length > 0 && movies[0] ? 
              'Được đề xuất dựa trên sở thích và lịch sử xem phim của bạn' :
              'Danh sách phim phổ biến dành cho bạn'
            }
          </p>
        </div>
      </div>

      {movies.length === 0 ? (
        <div className={styles.noMovies}>
          <p>Chưa có phim đề xuất. Hãy xem và đánh giá một số phim để nhận được gợi ý!</p>
        </div>
      ) : (
        <div className={styles.moviesGrid}>
          {movies.map((movie) => (
            <div className={styles.movieCard} key={movie.id}>
              <img 
                src={movie.poster_link} 
                alt={movie.series_title} 
                className={styles.poster} 
              />
              <div className={styles.movieInfo}>
                <p className={styles.movieTitle}>{movie.series_title}</p>
                <div className={styles.rating}>
                  ⭐ {movie.imdb_rating} / 10
                </div>
                <div className={styles.movieButtons}>
                  <button 
                    className={styles.btnBuy}
                    onClick={() => handleBuyClick(movie.series_title, movie.id)}
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
      )}

      <BookingPopup 
        isOpen={isBookingOpen}
        onClose={() => setIsBookingOpen(false)}
        movieTitle={selectedMovieTitle}
        movieId={selectedMovieId}
      />
    </div>
  );
}
