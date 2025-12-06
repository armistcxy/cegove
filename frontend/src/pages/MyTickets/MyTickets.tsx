import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './MyTickets.module.css';

interface Ticket {
  id: string;
  movieTitle: string;
  movieId?: number;
  cinema: string;
  cinemaAddress: string;
  date: string;
  showtime: string;
  bookingDate: string;
}

export default function MyTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleMovieClick = (movieId?: number) => {
    if (movieId) {
      navigate(`/MovieDetail/${movieId}`);
    }
  };

  const handleCancelTicket = (ticketId: string, movieTitle: string) => {
    const confirmed = window.confirm(`Bạn có chắc chắn muốn hủy vé phim "${movieTitle}" không?`);
    
    if (confirmed) {
      try {
        const updatedTickets = tickets.filter(ticket => ticket.id !== ticketId);
        setTickets(updatedTickets);
        localStorage.setItem('myTickets', JSON.stringify(updatedTickets));
        alert('Hủy vé thành công!');
      } catch (error) {
        console.error('Error canceling ticket:', error);
        alert('Có lỗi xảy ra khi hủy vé. Vui lòng thử lại.');
      }
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = () => {
    setLoading(true);
    try {
      const savedTickets = localStorage.getItem('myTickets');
      if (savedTickets) {
        const parsedTickets = JSON.parse(savedTickets);
        // Sort by booking date (newest first)
        parsedTickets.sort((a: Ticket, b: Ticket) => 
          new Date(b.bookingDate).getTime() - new Date(a.bookingDate).getTime()
        );
        setTickets(parsedTickets);
      }
    } catch (error) {
      console.error('Error loading tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBookingDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isUpcoming = (dateString: string, showtime: string) => {
    // Parse date string (format: DD/MM/YYYY)
    const [day, month, year] = dateString.split('/').map(Number);
    const ticketDate = new Date(year, month - 1, day);
    
    // Parse showtime (format: HH:MM)
    const [hours, minutes] = showtime.split(':').map(Number);
    ticketDate.setHours(hours, minutes, 0, 0);
    
    // Compare with current date and time
    const now = new Date();
    return ticketDate > now;
  };

  const upcomingTickets = tickets.filter(ticket => isUpcoming(ticket.date, ticket.showtime));
  const pastTickets = tickets.filter(ticket => !isUpcoming(ticket.date, ticket.showtime));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Vé Của Tôi</h1>
        <p>Quản lý và xem lại các vé đã đặt</p>
      </div>

      {loading ? (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Đang tải danh sách vé...</p>
        </div>
      ) : tickets.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>🎬</div>
          <h2>Chưa có vé nào</h2>
          <p>Bạn chưa đặt vé phim nào. Hãy khám phá các bộ phim đang chiếu và đặt vé ngay!</p>
          <a href="/movie" className={styles.browseButton}>
            Khám phá phim
          </a>
        </div>
      ) : (
        <>
          {upcomingTickets.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>
                Vé đã đặt ({upcomingTickets.length})
              </h2>
              <div className={styles.ticketGrid}>
                {upcomingTickets.map((ticket) => (
                  <div key={ticket.id} className={`${styles.ticketCard} ${styles.upcoming}`}>
                    <div className={styles.ticketHeader}>
                      <h3 
                        className={`${styles.movieTitle} ${ticket.movieId ? styles.clickable : ''}`}
                        onClick={() => handleMovieClick(ticket.movieId)}
                      >
                        {ticket.movieTitle}
                      </h3>
                      <span className={styles.statusBadge}>Sắp chiếu</span>
                    </div>
                    
                    <div className={styles.ticketInfo}>
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <div>
                          <p className={styles.cinema}>{ticket.cinema}</p>
                          <p className={styles.address}>{ticket.cinemaAddress}</p>
                        </div>
                      </div>
                      
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className={styles.datetime}>
                          <span className={styles.date}>{ticket.date}</span>
                          <span className={styles.time}>{ticket.showtime}</span>
                        </p>
                      </div>
                      
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                        </svg>
                        <p className={styles.bookingDate}>
                          Đặt vào: {formatBookingDate(ticket.bookingDate)}
                        </p>
                      </div>
                    </div>
                    
                    <div className={styles.ticketActions}>
                      {ticket.movieId && (
                        <button 
                          className={styles.detailButton}
                          onClick={() => handleMovieClick(ticket.movieId)}
                        >
                          Xem chi tiết phim
                        </button>
                      )}
                      <button 
                        className={styles.cancelButton}
                        onClick={() => handleCancelTicket(ticket.id, ticket.movieTitle)}
                      >
                        Hủy vé
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {pastTickets.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>
                Vé đã xem ({pastTickets.length})
              </h2>
              <div className={styles.ticketGrid}>
                {pastTickets.map((ticket) => (
                  <div key={ticket.id} className={`${styles.ticketCard} ${styles.past}`}>
                    <div className={styles.ticketHeader}>
                      <h3 
                        className={`${styles.movieTitle} ${ticket.movieId ? styles.clickable : ''}`}
                        onClick={() => handleMovieClick(ticket.movieId)}
                      >
                        {ticket.movieTitle}
                      </h3>
                      <span className={styles.statusBadge}>Đã xem</span>
                    </div>
                    
                    <div className={styles.ticketInfo}>
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <div>
                          <p className={styles.cinema}>{ticket.cinema}</p>
                          <p className={styles.address}>{ticket.cinemaAddress}</p>
                        </div>
                      </div>
                      
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className={styles.datetime}>
                          <span className={styles.date}>{ticket.date}</span>
                          <span className={styles.time}>{ticket.showtime}</span>
                        </p>
                      </div>
                      
                      <div className={styles.infoRow}>
                        <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                        </svg>
                        <p className={styles.bookingDate}>
                          Đặt vào: {formatBookingDate(ticket.bookingDate)}
                        </p>
                      </div>
                    </div>
                    
                    {ticket.movieId && (
                      <button 
                        className={styles.detailButton}
                        onClick={() => handleMovieClick(ticket.movieId)}
                      >
                        Xem chi tiết phim
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
