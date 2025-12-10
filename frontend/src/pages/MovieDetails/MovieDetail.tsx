import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Movie } from "../Movies/MovieLogic.ts";
import { fetchMovieDetail, fetchSimilarMovies } from "./MovieDetailLogic.ts";
import BookingPopup from "../../components/BookingPopup/BookingPopup.tsx";
import RelatedMoviesSlider from "../../components/RelatedMoviesSlider/RelatedMoviesSlider.tsx";
import styles from "./MovieDetail.module.css";

export default function MovieDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [similarMovies, setSimilarMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBookingPopupOpen, setIsBookingPopupOpen] = useState(false);
  const [selectedMovieTitle, setSelectedMovieTitle] = useState<string>("");
  const [selectedMovieId, setSelectedMovieId] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!id) {
      setError("Movie ID not found");
      setLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        const [movieData, similarData] = await Promise.all([
          fetchMovieDetail(id),
          fetchSimilarMovies(id, 20)
        ]);

        if (movieData) {
          setMovie(movieData);
        } else {
          setError("Movie not found");
        }

        setSimilarMovies(similarData);
      } catch (err) {
        setError("Failed to load movie details");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Đang tải thông tin phim...</p>
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
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            ← Quay lại danh sách phim
          </button>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Không tìm thấy phim</h2>
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            ← Quay lại danh sách phim
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <button 
        className={styles.backButton}
        onClick={() => navigate('/movie')}
      >
        ← Quay lại danh sách phim
      </button>
      
      <div className={styles.movieDetail}>
        <div className={styles.posterSection}>
          <img 
            src={movie.poster_link} 
            alt={movie.series_title}
            className={styles.poster}
          />
        </div>
        
        <div className={styles.infoSection}>
          <h1 className={styles.title}>{movie.series_title}</h1>
          
          <div className={styles.metadata}>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Năm</span>
              <span className={styles.metaValue}>{movie.released_year}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Thời lượng</span>
              <span className={styles.metaValue}>{movie.runtime}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Phân loại</span>
              <span className={styles.metaValue}>{movie.certificate}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Đánh giá IMDb</span>
              <span className={styles.metaValue}>⭐ {movie.imdb_rating}/10</span>
            </div>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Thể loại</h3>
            <p className={styles.genre}>{movie.genre}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Tóm tắt</h3>
            <p className={styles.overview}>{movie.overview}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Đạo diễn</h3>
            <p className={styles.director}>{movie.director}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Diễn viên</h3>
            <div className={styles.cast}>
              {[movie.star1, movie.star2, movie.star3, movie.star4]
                .filter(star => star && star.trim() !== '')
                .map((star, index) => (
                  <span key={index} className={styles.castMember}>
                    {star}
                  </span>
                ))
              }
            </div>
          </div>
          
          <div className={styles.actions}>
            <button 
              className={styles.buyButton}
              onClick={() => setIsBookingPopupOpen(true)}
            >
              Mua vé
            </button>
            <button className={styles.watchlistButton}>
              Thêm vào danh sách
            </button>
          </div>
        </div>
      </div>

      {/* Booking Popup */}
      <BookingPopup 
        isOpen={isBookingPopupOpen}
        onClose={() => setIsBookingPopupOpen(false)}
        movieTitle={selectedMovieTitle}
        movieId={selectedMovieId}
      />

      {/* Related Movies Slider */}
      <RelatedMoviesSlider 
        movies={similarMovies}
        onBuyClick={(title, movieId) => {
          setSelectedMovieTitle(title);
          setSelectedMovieId(movieId);
          setIsBookingPopupOpen(true);
        }}
      />
    </div>
  );
}