import { useEffect, useState } from "react";
import type { Movie } from "./MovieLogic";
import { fetchMovies } from "./MovieLogic";
import styles from "./Movie.module.css";

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([]);

  useEffect(() => {
    fetchMovies().then((data) => setMovies(data));
  }, []);

  return (
    <div className={styles.moviesSection}>
      <h2>Phim Đang Chiếu</h2>
      <div className={styles.moviesGrid}>
        {movies.map((m) => (
          <div className={styles.movieCard} key={m.id}>
            <img src={m.poster_link} alt={m.series_title} className={styles.poster} />
            <div className={styles.movieInfo}>
              <p className={styles.movieTitle}>{m.series_title}</p>
              <div className={styles.movieButtons}>
                <button className={styles.btnBuy}>Buy</button>
                <button className={styles.btnDetail}>Detail</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
