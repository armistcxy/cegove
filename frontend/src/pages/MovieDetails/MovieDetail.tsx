import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Movie } from "../Movies/MovieLogic.ts";
import { fetchMovieDetail } from "./MovieDetailLogic.ts";
import styles from "./MovieDetail.module.css";

export default function MovieDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError("Movie ID not found");
      setLoading(false);
      return;
    }

    fetchMovieDetail(id)
      .then((data) => {
        if (data) {
          setMovie(data);
        } else {
          setError("Movie not found");
        }
      })
      .catch(() => {
        setError("Failed to load movie details");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading movie details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Error</h2>
          <p>{error}</p>
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            Back to Movies
          </button>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Movie not found</h2>
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            Back to Movies
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
        ← Back to Movies
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
              <span className={styles.metaLabel}>Year:</span>
              <span className={styles.metaValue}>{movie.released_year}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Runtime:</span>
              <span className={styles.metaValue}>{movie.runtime}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Certificate:</span>
              <span className={styles.metaValue}>{movie.certificate}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>IMDb Rating:</span>
              <span className={styles.metaValue}>⭐ {movie.imdb_rating}/10</span>
            </div>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Genre</h3>
            <p className={styles.genre}>{movie.genre}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Overview</h3>
            <p className={styles.overview}>{movie.overview}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Director</h3>
            <p className={styles.director}>{movie.director}</p>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Cast</h3>
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
            <button className={styles.buyButton}>
              Buy Ticket
            </button>
            <button className={styles.watchlistButton}>
              Add to Watchlist
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}