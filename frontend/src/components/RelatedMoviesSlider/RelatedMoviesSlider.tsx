import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import type { Movie } from "../../pages/Movies/MovieLogic";
import styles from "./RelatedMoviesSlider.module.css";

interface RelatedMoviesSliderProps {
  movies: Movie[];
  onBuyClick: (movieTitle: string, movieId: number) => void;
}

export default function RelatedMoviesSlider({ movies, onBuyClick }: RelatedMoviesSliderProps) {
  const navigate = useNavigate();
  const sliderRef = useRef<HTMLDivElement>(null);

  const scrollLeft = () => {
    if (sliderRef.current) {
      sliderRef.current.scrollBy({
        left: -800,
        behavior: "smooth"
      });
    }
  };

  const scrollRight = () => {
    if (sliderRef.current) {
      sliderRef.current.scrollBy({
        left: 800,
        behavior: "smooth"
      });
    }
  };

  const handleDetailClick = (movieId: number) => {
    navigate(`/MovieDetail/${movieId}`);
    window.scrollTo(0, 0);
  };

  if (movies.length === 0) {
    return null;
  }

  return (
    <div className={styles.sliderContainer}>
      <h2 className={styles.title}>Phim liên quan</h2>
      
      <div className={styles.sliderWrapper}>
        <button 
          className={`${styles.navButton} ${styles.navButtonLeft}`}
          onClick={scrollLeft}
          aria-label="Trượt sang trái"
        >
          ‹
        </button>
        
        <div className={styles.slider} ref={sliderRef}>
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
                  ⭐ {movie.imdb_rating}
                </div>
                <div className={styles.movieButtons}>
                  <button 
                    className={styles.btnBuy}
                    onClick={() => onBuyClick(movie.series_title, movie.id)}
                  >
                    Mua vé
                  </button>
                  <button 
                    className={styles.btnDetail}
                    onClick={() => handleDetailClick(movie.id)}
                  >
                    Chi tiết
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <button 
          className={`${styles.navButton} ${styles.navButtonRight}`}
          onClick={scrollRight}
          aria-label="Trượt sang phải"
        >
          ›
        </button>
      </div>
    </div>
  );
}
