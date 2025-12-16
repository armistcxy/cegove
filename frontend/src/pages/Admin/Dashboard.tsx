import styles from './Admin.module.css';
import { useEffect, useState } from 'react';
import { fetchTotalMovies, fetchTotalCinemas } from './DashboardLogic';
import { fetchTotalUsers } from './Utils/UserApi';

export default function Dashboard() {
  const [totalMovies, setTotalMovies] = useState<number | null>(null);
  const [totalCinemas, setTotalCinemas] = useState<number | null>(null);
  const [totalUsers, setTotalUsers] = useState<number | null>(null);

  useEffect(() => {
    fetchTotalMovies().then(setTotalMovies);
    fetchTotalCinemas().then(setTotalCinemas);
    const token = localStorage.getItem('access-token') || '';
    fetchTotalUsers(token).then(setTotalUsers);
  }, []);

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>Dashboard</h1>
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <div className={styles.statInfo}>
            <h3>Total Users</h3>
            <p className={styles.statNumber}>{totalUsers !== null ? totalUsers : '...'}</p>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
          </div>
          <div className={styles.statInfo}>
            <h3>Total Movies</h3>
            <p className={styles.statNumber}>{totalMovies !== null ? totalMovies : '...'}</p>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div className={styles.statInfo}>
            <h3>Total Cinemas</h3>
            <p className={styles.statNumber}>{totalCinemas !== null ? totalCinemas : '...'}</p>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
          </div>
          <div className={styles.statInfo}>
            <h3>Bookings Today</h3>
            <p className={styles.statNumber}>189</p>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Activities</h2>
        <div className={styles.card}>
          <p className={styles.placeholder}>Dashboard content coming soon...</p>
        </div>
      </div>
    </div>
  );
}
