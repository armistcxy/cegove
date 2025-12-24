
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './MyTickets.module.css';

interface TicketDetail {
  id: string;
  bookingId: string;
  seatNumber: string;
  price: number;
}

interface Ticket {
  id: string;
  movieTitle: string;
  movieId?: number;
  cinema: string;
  cinemaAddress: string;
  date: string;
  showtime: string;
  endTime: string;
  bookingDate: string;
  totalPrice: number;
  tickets: TicketDetail[];
}

export default function MyTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  // Lưu map movieTitle -> movieId
  const [movieIdMap, setMovieIdMap] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleMovieClick = (movieTitle?: string, movieId?: number) => {
    // Ưu tiên movieId, nếu không có thì thử lấy từ map
    const id = movieId ?? (movieTitle ? movieIdMap[movieTitle] : undefined);
    if (id) {
      navigate(`/MovieDetail/${id}`);
    } else {
      alert('Không tìm thấy thông tin phim!');
    }
  };
  // Hàm lấy movieId từ API theo tên phim
  const fetchMovieIdByTitle = async (title: string): Promise<number | undefined> => {
    try {
      const resp = await fetch(`https://movies.cegove.cloud/api/v1/movies/search?q=${encodeURIComponent(title)}&limit=1`, {
        headers: { 'accept': 'application/json' }
      });
      if (!resp.ok) return undefined;
      const data = await resp.json();
      if (Array.isArray(data) && data.length > 0 && data[0].id) {
        return data[0].id;
      }
      // Nếu data có dạng { data: [...] }
      if (data.data && Array.isArray(data.data) && data.data.length > 0 && data.data[0].id) {
        return data.data[0].id;
      }
      return undefined;
    } catch {
      return undefined;
    }
  };




  useEffect(() => {
    fetchTickets();
    // eslint-disable-next-line
  }, []);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access-token');
      if (!token) {
        setTickets([]);
        setLoading(false);
        return;
      }
      const response = await fetch('https://user.cegove.cloud/users/booking-history', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch tickets');
      const data = await response.json();
      // data is an array of bookings
      const ticketsData = (Array.isArray(data) ? data : []).map((b: any) => ({
        id: b.id,
        movieTitle: b.movieTitle || '',
        movieId: undefined, // sẽ cập nhật sau
        cinema: b.cinemaName || '',
        cinemaAddress: b.auditoriumName || '',
        date: formatDate(b.startTime),
        showtime: formatTime(b.startTime),
        endTime: formatTime(b.endTime),
        bookingDate: b.createdAt || '',
        totalPrice: b.totalPrice || 0,
        tickets: Array.isArray(b.tickets) ? b.tickets.map((t: any) => ({
          id: t.id,
          bookingId: t.bookingId,
          seatNumber: t.seatNumber,
          price: t.price
        })) : [],
      }));
      // Sort by booking date (newest first)
      ticketsData.sort((a: Ticket, b: Ticket) => new Date(b.bookingDate).getTime() - new Date(a.bookingDate).getTime());
      setTickets(ticketsData);

      // Tìm movieId cho từng movieTitle (nếu chưa có)
      const uniqueTitles = Array.from(new Set(ticketsData.map(t => t.movieTitle).filter(Boolean)));
      const idMap: Record<string, number> = {};
      await Promise.all(uniqueTitles.map(async (title) => {
        const id = await fetchMovieIdByTitle(title);
        if (id) idMap[title] = id;
      }));
      setMovieIdMap(idMap);
    } catch (error) {
      console.error('Error fetching tickets:', error);
      setTickets([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper to format ISO date string to DD/MM/YYYY
  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('vi-VN');
  };

  // Helper to format ISO date string to HH:mm
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false });
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
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 320,
          width: '100%',
          marginTop: 48,
        }}>
          <div style={{
            width: 64,
            height: 64,
            border: '6px solid #ffe5e9',
            borderTop: '6px solid #e50914',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginBottom: 18,
          }} />
          <div style={{color: '#b20710', fontWeight: 700, fontSize: '1.1em'}}>Đang tải danh sách vé...</div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
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
                  <div
                    key={ticket.id}
                    className={`${styles.ticketCard} ${styles.upcoming}`}
                    style={{
                      border: '3px solid #f4433633',
                      borderRadius: 16,
                      background: '#fff',
                    }}
                  >
                    <div className={styles.ticketHeader}>
                      <h3 
                        className={`${styles.movieTitle} ${ticket.movieId ? styles.clickable : ''}`}
                        onClick={() => handleMovieClick(ticket.movieTitle, ticket.movieId)}
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
                          <span className={styles.time}>{ticket.showtime} - {ticket.endTime}</span>
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
                      <div className={styles.infoRow}>
                        <span className={styles.label}>Tổng tiền:</span>
                        <span>{ticket.totalPrice.toLocaleString('vi-VN')} đ</span>
                      </div>
                    </div>
                    <div className={styles.ticketActions}>
                      <button 
                        className={styles.detailButton}
                        onClick={() => navigate(`/my-tickets/${ticket.id}`)}
                      >
                        Xem chi tiết
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
                  <div
                    key={ticket.id}
                    className={`${styles.ticketCard} ${styles.past}`}
                    style={{
                      border: '2px solid #f4433633',
                      borderRadius: 16,
                      background: '#fff',
                    }}
                  >
                    <div className={styles.ticketHeader}>
                      <h3 
                        className={`${styles.movieTitle} ${ticket.movieId ? styles.clickable : ''}`}
                        onClick={() => handleMovieClick(ticket.movieTitle, ticket.movieId)}
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
                          <span className={styles.time}>{ticket.showtime} - {ticket.endTime}</span>
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
                      <div className={styles.infoRow}>
                        <span className={styles.label}>Tổng tiền:</span>
                        <span>{ticket.totalPrice.toLocaleString('vi-VN')} đ</span>
                      </div>
                    </div>
                    <div className={styles.ticketActions}>
                      <button 
                        className={styles.detailButton}
                        onClick={() => navigate(`/my-tickets/${ticket.id}`)}
                      >
                        Xem chi tiết
                      </button>
                    </div>
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
