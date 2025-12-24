import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './MyTickets.module.css';

interface TicketDetail {
  id: string;
  bookingId: string;
  seatNumber: string;
  price: number;
}

interface FoodItem {
  food_item_id: string;
  quantity: number;
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
  food_items?: FoodItem[];
}

interface FoodDetail {
  id: string;
  name: string;
  type: string;
  category: string;
  price: number;
  image_url: string;
  available: boolean;
  created_at: string;
}

export default function MyTicketDetail() {
  const { id } = useParams<{ id: string }>();
  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [foodDetails, setFoodDetails] = useState<{ [id: string]: FoodDetail }>({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();


  useEffect(() => {
    if (!id) return;
    setLoading(true);
    // Gọi endpoint booking detail để lấy food_items
    fetch(`https://booking.cegove.cloud/api/v1/bookings/${id}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (!data) {
          setBooking(null);
          return;
        }
        setBooking({
          id: data.id,
          totalPrice: data.total_price,
          movieTitle: data.tickets?.[0]?.movie_title || '',
          cinemaName: data.tickets?.[0]?.cinema_name || '',
          auditoriumName: data.tickets?.[0]?.auditorium_name || '',
          startTime: data.tickets?.[0]?.showtime || '',
          endTime: '',
          createdAt: data.created_at,
          tickets: Array.isArray(data.tickets) ? data.tickets.map((t: any) => ({
            id: t.id,
            bookingId: t.booking_id,
            seatNumber: t.seat_number,
            price: t.price,
          })) : [],
          food_items: Array.isArray(data.food_items) ? data.food_items : [],
        });
        // Lấy thông tin từng food item
        if (Array.isArray(data.food_items)) {
          data.food_items.forEach((item: any) => {
            if (!item.food_item_id) return;
            setFoodDetails(prev => {
              if (prev[item.food_item_id]) return prev;
              // fetch food detail nếu chưa có
              fetch(`https://booking.cegove.cloud/api/v1/food/items/${item.food_item_id}`)
                .then(res => res.ok ? res.json() : null)
                .then(food => {
                  if (food && food.id) {
                    setFoodDetails(p => ({ ...p, [food.id]: food }));
                  }
                });
              return prev;
            });
          });
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

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

      {/* Hiển thị food items nếu có - moved above tickets */}
      {booking?.food_items && booking.food_items.length > 0 && (
        <div style={{
          margin: '32px auto 0 auto',
          maxWidth: 1000,
          width: '95%',
          background: '#fff8f2',
          borderRadius: 16,
          boxShadow: '0 2px 12px #e5091422',
          padding: 32,
        }}>
          <h3 style={{color: '#b20710', fontWeight: 700, marginBottom: 16}}>Đồ ăn kèm</h3>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 18,
            justifyContent: 'flex-start',
          }}>
            {booking.food_items.map(item => {
              const food = foodDetails[item.food_item_id];
              return (
                <div key={item.food_item_id} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-start',
                  background: '#fff',
                  borderRadius: 10,
                  boxShadow: '0 1px 6px #e5091422',
                  padding: 14,
                  minWidth: 270,
                  maxWidth: 320,
                  width: '30%',
                  flex: '1 1 30%',
                  height: 110,
                  gap: 16,
                  boxSizing: 'border-box',
                }}>
                  {food?.image_url ? (
                    <img src={food.image_url} alt={food.name} style={{width: 60, height: 60, objectFit: 'cover', borderRadius: 8, border: '1.5px solid #ffe5e9', background: '#fff'}} />
                  ) : (
                    <div style={{width: 60, height: 60, background: '#ffe5e9', borderRadius: 8}} />
                  )}
                  <div style={{flex: 1}}>
                    <div style={{
                      fontWeight: 700,
                      color: '#b20710',
                      fontSize: 16,
                      wordBreak: 'break-word',
                      whiteSpace: 'normal',
                      lineHeight: 1.25,
                      overflowWrap: 'anywhere',
                      maxWidth: 220,
                    }}>{food?.name || item.food_item_id}</div>
                    <div style={{color: '#888', fontSize: 13}}>{food?.category || ''}</div>
                    <div style={{color: '#b20710', fontWeight: 600, fontSize: 15}}>{item.price.toLocaleString('vi-VN')} đ x {item.quantity}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
