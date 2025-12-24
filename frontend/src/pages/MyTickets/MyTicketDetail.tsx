import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './MyTickets.module.css';

interface TicketDetail {
  id: string;
  bookingId: string;
  seatNumber: string;
  price: number;
}

interface BookingDetail {
  id: string;
  totalPrice: number;
  movieTitle: string;
  cinemaName: string;
  auditoriumName: string;
  startTime: string;
  endTime: string;
  createdAt: string;
  tickets: TicketDetail[];
}

export default function MyTicketDetail() {
  const { id } = useParams<{ id: string }>();
  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchBooking();
    // eslint-disable-next-line
  }, [id]);

  const fetchBooking = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access-token');
      if (!token) {
        setBooking(null);
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
      if (!response.ok) throw new Error('Failed to fetch booking');
      const data = await response.json();
      const found = (Array.isArray(data) ? data : []).find((b: any) => b.id === id);
      if (!found) {
        setBooking(null);
      } else {
        setBooking({
          id: found.id,
          totalPrice: found.totalPrice,
          movieTitle: found.movieTitle,
          cinemaName: found.cinemaName,
          auditoriumName: found.auditoriumName,
          startTime: found.startTime,
          endTime: found.endTime,
          createdAt: found.createdAt,
          tickets: Array.isArray(found.tickets) ? found.tickets : [],
        });
      }
    } catch (error) {
      setBooking(null);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('vi-VN');
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  return (
    <div className={styles.container}>
      <button
        onClick={() => navigate(-1)}
        style={{
          background: 'linear-gradient(90deg, #e50914 70%, #b20710 100%)',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          padding: '10px 28px',
          fontWeight: 700,
          fontSize: '1.1em',
          boxShadow: '0 2px 12px #b2071040',
          cursor: 'pointer',
          marginTop: 12,
          marginBottom: 0,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          transition: 'transform 0.15s, box-shadow 0.15s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.transform = 'scale(1.04)';
          e.currentTarget.style.boxShadow = '0 4px 18px #e5091440';
        }}
        onMouseLeave={e => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 2px 12px #b2071040';
        }}
      >
        <span style={{fontSize: '1.2em', verticalAlign: 'middle', marginRight: 4}}>&larr;</span> Quay lại
      </button>

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
          <div style={{color: '#b20710', fontWeight: 700, fontSize: '1.1em'}}>Đang tải vé của bạn...</div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : (
        <div style={{display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 24, justifyContent: 'center', marginTop: 24}}>
          {booking?.tickets.map(ticket => (
            <div
              key={ticket.id}
              className={styles.ticketDetailCard}
              style={{
                minWidth: 380,
                maxWidth: 480,
                margin: 16,
                background: 'linear-gradient(120deg, #fff 60%, #ffe5e9 100%)',
                borderRadius: 24,
                boxShadow: '0 8px 32px 0 rgba(229,9,20,0.18), 0 1.5px 8px 0 #e5091422',
                border: 'none',
                position: 'relative',
                overflow: 'visible',
                padding: 0,
                display: 'flex',
                flexDirection: 'row',
                transition: 'transform 0.2s cubic-bezier(.4,2,.6,1)',
                cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.025)')}
              onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
            >
              {/* Main ticket section */}
              <div style={{
                flex: 3,
                padding: '24px 24px 20px 32px',
                borderTopLeftRadius: 24,
                borderBottomLeftRadius: 24,
                background: 'rgba(255,255,255,0.92)',
                position: 'relative',
                zIndex: 2,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}>
                <div style={{textAlign: 'center', marginBottom: 12}}>
                  <span style={{
                    display: 'inline-block',
                    marginBottom: 2,
                    filter: 'drop-shadow(0 2px 8px #e5091440)'
                  }}>
                    <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <defs>
                        <linearGradient id="classicTicketRed" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                          <stop stopColor="#e50914"/>
                          <stop offset="1" stopColor="#b20710"/>
                        </linearGradient>
                      </defs>
                      <path d="M8 12 Q8 8 12 8 H36 Q40 8 40 12 V16 A4 4 0 0 1 40 24 A4 4 0 0 1 40 32 V36 Q40 40 36 40 H12 Q8 40 8 36 V32 A4 4 0 0 1 8 24 A4 4 0 0 1 8 16 Z" fill="url(#classicTicketRed)" stroke="#b20710" strokeWidth="2"/>
                      <rect x="16" y="20" width="16" height="8" rx="2" fill="#fff2" stroke="#fff" strokeWidth="1.2"/>
                      <rect x="20" y="23" width="8" height="2" rx="1" fill="#fff"/>
                      <rect x="20" y="26" width="5" height="2" rx="1" fill="#fff"/>
                      <circle cx="12" cy="24" r="2.2" fill="#fff" stroke="#b20710" strokeWidth="1"/>
                      <circle cx="36" cy="24" r="2.2" fill="#fff" stroke="#b20710" strokeWidth="1"/>
                    </svg>
                  </span>
                  <h2 style={{
                    fontWeight: 800,
                    fontSize: '1.3rem',
                    color: '#b20710',
                    margin: 0,
                    letterSpacing: 1.2,
                    textShadow: '0 1px 8px #fff, 0 2px 8px #e5091422',
                  }}>{booking.movieTitle || 'Chi tiết đặt vé'}</h2>
                </div>
                <div style={{
                  width: '100%',
                  height: 0,
                  borderTop: '1.5px dashed #e50914',
                  margin: '0 0 12px 0',
                  opacity: 0.7,
                }} />
                <div style={{marginBottom: 8}}>
                  <div className={styles.infoRow}><b>Rạp:</b> <span style={{color:'#b20710', fontWeight:600}}>{booking.cinemaName}</span></div>
                  <div className={styles.infoRow}><b>Phòng chiếu:</b> <span style={{color:'#b20710', fontWeight:600}}>{booking.auditoriumName}</span></div>
                  <div className={styles.infoRow}><b>Ngày chiếu:</b> <span style={{color:'#b20710', fontWeight:600}}>{formatDate(booking.startTime)}</span></div>
                  <div className={styles.infoRow}><b>Giờ chiếu:</b> <span style={{color:'#b20710', fontWeight:600}}>{formatTime(booking.startTime)} - {formatTime(booking.endTime)}</span></div>
                  <div className={styles.infoRow}><b>Ghế:</b> <span style={{fontWeight:800, color:'#e50914', fontSize:'1.2em', letterSpacing:2, textShadow:'0 1px 8px #fff'}}>{ticket.seatNumber}</span></div>
                  <div className={styles.infoRow}><b>Giá:</b> <span style={{color:'#e50914', fontWeight:800, fontSize:'1.1em', textShadow:'0 1px 8px #fff'}}>{ticket.price.toLocaleString('vi-VN')} đ</span></div>
                </div>
                <div style={{marginTop: 8}}>
                  <div className={styles.infoRow}><b>Mã vé:</b> <span style={{color:'#888', fontFamily:'monospace', fontSize:'1em', letterSpacing:1, background:'#fff6', borderRadius:6, padding:'2px 8px'}}>{ticket.id}</span></div>
                  <div className={styles.infoRow}><b>Đặt lúc:</b> <span style={{color:'#b20710', fontWeight:600}}>{formatDate(booking.createdAt)}</span></div>
                </div>
              </div>
              {/* Perforation stub section */}
              <div style={{
                flex: 1.1,
                minWidth: 90,
                maxWidth: 120,
                background: 'repeating-linear-gradient(135deg, #ffe5e9 0 12px, #fff 12px 24px)',
                borderTopRightRadius: 24,
                borderBottomRightRadius: 24,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                zIndex: 1,
                borderLeft: '2.5px dashed #e50914',
                boxShadow: '-2px 0 8px #e5091422',
                padding: '0 8px',
              }}>
                {/* Circle cutout effect for stub */}
                <div style={{
                  position: 'absolute',
                  left: -16,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: 32,
                  height: 32,
                  background: '#fff',
                  borderRadius: '50%',
                  border: '2.5px solid #e50914',
                  zIndex: 4,
                  boxShadow: '0 2px 8px #e5091422',
                }} />
                {/* Barcode simulation */}
                <div style={{margin: '18px 0 8px 0', width: 60, height: 40, background: '#fff', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 1px 4px #e5091422'}}>
                  <svg width="54" height="32" viewBox="0 0 54 32" style={{display:'block'}}>
                    <rect x="0" y="0" width="54" height="32" fill="#fff" />
                    <rect x="2" y="4" width="2" height="24" fill="#222" />
                    <rect x="6" y="4" width="1" height="24" fill="#222" />
                    <rect x="9" y="4" width="3" height="24" fill="#222" />
                    <rect x="14" y="4" width="1" height="24" fill="#222" />
                    <rect x="17" y="4" width="2" height="24" fill="#222" />
                    <rect x="21" y="4" width="1" height="24" fill="#222" />
                    <rect x="24" y="4" width="4" height="24" fill="#222" />
                    <rect x="30" y="4" width="1" height="24" fill="#222" />
                    <rect x="33" y="4" width="2" height="24" fill="#222" />
                    <rect x="37" y="4" width="1" height="24" fill="#222" />
                    <rect x="40" y="4" width="3" height="24" fill="#222" />
                    <rect x="45" y="4" width="1" height="24" fill="#222" />
                    <rect x="48" y="4" width="2" height="24" fill="#222" />
                  </svg>
                </div>
                <div style={{fontSize: '0.85em', color: '#b20710', fontWeight: 700, letterSpacing: 1, textAlign: 'center', marginBottom: 6, marginTop: 2}}>
                  Vé xem phim
                </div>
                <div style={{fontSize: '0.7em', color: '#888', fontFamily: 'monospace', textAlign: 'center', wordBreak: 'break-all'}}>{ticket.id}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
