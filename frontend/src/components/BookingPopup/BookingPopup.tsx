import { useState, useEffect } from 'react';
import { fetchCinemas } from '../../pages/Cinemas/CinemaLogic';
import styles from './BookingPopup.module.css';

interface Cinema {
  id?: number;
  name: string;
  address: string;
  city: string;
  district: string;
}

interface CinemaWithId extends Cinema {
  uniqueId: string;
}

interface BookingPopupProps {
  isOpen: boolean;
  onClose: () => void;
  movieTitle: string;
  movieId?: number;
}

const SHOWTIMES = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'];

export default function BookingPopup({ isOpen, onClose, movieTitle, movieId }: BookingPopupProps) {
  const [step, setStep] = useState<'city' | 'cinema'>('city');
  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [cinemas, setCinemas] = useState<CinemaWithId[]>([]);
  const [selectedCinema, setSelectedCinema] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedShowtime, setSelectedShowtime] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // Generate next 14 days (2 weeks) for date selection
  const getNext14Days = () => {
    const days = [];
    const today = new Date();
    for (let i = 0; i < 14; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const formatDate = (date: Date) => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${day}/${month}`;
  };

  const getDayName = (date: Date) => {
    const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
    return days[date.getDay()];
  };

  const getDateValue = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  useEffect(() => {
    if (isOpen) {
      loadCities();
      // Set default date to today
      setSelectedDate(getDateValue(new Date()));
    } else {
      // Reset state when popup closes
      setStep('city');
      setSelectedCity('');
      setSelectedCinema(null);
      setSelectedDate('');
      setSelectedShowtime('');
    }
  }, [isOpen]);

  const loadCities = async () => {
    setLoading(true);
    try {
      const allCinemas = await fetchCinemas();
      
      // Add unique IDs to each cinema since API doesn't provide them
      const cinemasWithIds: CinemaWithId[] = allCinemas.map((cinema, index) => ({
        ...cinema,
        uniqueId: cinema.id?.toString() || `${cinema.city}-${cinema.name}-${index}`
      }));
      
      const uniqueCities = [...new Set(cinemasWithIds.map(c => c.city))];
      setCities(uniqueCities.sort());
      setCinemas(cinemasWithIds);
    } catch (error) {
      console.error('Error loading cities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCitySelect = (city: string) => {
    setSelectedCity(city);
    setStep('cinema');
    setSelectedCinema(null);
    setSelectedShowtime('');
  };

  const handleDateSelect = (dateValue: string) => {
    setSelectedDate(dateValue);
    setSelectedCinema(null);
    setSelectedShowtime('');
  };

  const handleCinemaSelect = (cinemaId: string) => {
    if (selectedCinema === cinemaId) {
      // Unselect if clicking the same cinema
      setSelectedCinema(null);
      setSelectedShowtime('');
    } else {
      // Select new cinema and clear showtime
      setSelectedCinema(cinemaId);
      setSelectedShowtime('');
    }
  };

  const handleShowtimeSelect = (time: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setSelectedShowtime(time);
  };

  const handleConfirm = () => {
    if (selectedCinema && selectedShowtime && selectedDate) {
      const cinema = filteredCinemas.find(c => c.uniqueId === selectedCinema);
      const dateObj = new Date(selectedDate);
      const dateStr = `${dateObj.getDate().toString().padStart(2, '0')}/${(dateObj.getMonth() + 1).toString().padStart(2, '0')}/${dateObj.getFullYear()}`;
      
      // Create ticket object
      const ticket = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        movieTitle: movieTitle,
        movieId: movieId,
        cinema: cinema?.name || '',
        cinemaAddress: `${cinema?.address}, ${cinema?.district}` || '',
        date: dateStr,
        showtime: selectedShowtime,
        bookingDate: new Date().toISOString()
      };

      // Save to localStorage
      try {
        const existingTickets = localStorage.getItem('myTickets');
        const tickets = existingTickets ? JSON.parse(existingTickets) : [];
        tickets.push(ticket);
        localStorage.setItem('myTickets', JSON.stringify(tickets));
      } catch (error) {
        console.error('Error saving ticket:', error);
      }

      alert(`Đặt vé thành công!\n\nPhim: ${movieTitle}\nRạp: ${cinema?.name}\nNgày: ${dateStr}\nGiờ chiếu: ${selectedShowtime}\n\nCảm ơn bạn đã đặt vé tại CGV!`);
      onClose();
    }
  };

  const handleBack = () => {
    if (step === 'cinema') {
      setStep('city');
      setSelectedCity('');
      setSelectedCinema(null);
      setSelectedDate('');
      setSelectedShowtime('');
    }
  };

  const filteredCinemas = selectedCity 
    ? cinemas.filter(c => c.city === selectedCity)
    : [];

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <h2>{movieTitle}</h2>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Back Button - Outside Header */}
        {step === 'cinema' && (
          <div className={styles.backBtnContainer}>
            <button className={styles.backBtnOutside} onClick={handleBack}>
              ← Quay lại
            </button>
          </div>
        )}

        {/* Content */}
        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <p>Đang tải...</p>
            </div>
          ) : (
            <>
              {step === 'city' && (
                <div className={styles.citySelection}>
                  <h3>Chọn thành phố</h3>
                  <div className={styles.cityGrid}>
                    {cities.map((city) => (
                      <button
                        key={city}
                        className={`${styles.cityCard} ${selectedCity === city ? styles.selected : ''}`}
                        onClick={() => handleCitySelect(city)}
                      >
                        <span className={styles.cityIcon}>🎟️</span>
                        <span className={styles.cityName}>{city}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {step === 'cinema' && (
                <div className={styles.cinemaSelection}>
                  <h3>Chọn rạp và giờ chiếu tại {selectedCity}</h3>
                  
                  {/* Date Selection */}
                  <div className={styles.dateSelection}>
                    <p className={styles.dateLabel}>Chọn ngày chiếu:</p>
                    <div className={styles.dateGrid}>
                      {getNext14Days().map((date) => {
                        const dateValue = getDateValue(date);
                        const isToday = dateValue === getDateValue(new Date());
                        return (
                          <button
                            key={dateValue}
                            className={`${styles.dateBtn} ${selectedDate === dateValue ? styles.selected : ''}`}
                            onClick={() => handleDateSelect(dateValue)}
                          >
                            <span className={styles.dayName}>{getDayName(date)}</span>
                            <span className={styles.dateNumber}>{formatDate(date)}</span>
                            {isToday && <span className={styles.todayLabel}>Hôm nay</span>}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className={styles.cinemaList}>
                    {filteredCinemas.map((cinema) => {
                      const isThisCinemaSelected = selectedCinema === cinema.uniqueId;
                      return (
                        <div 
                          key={cinema.uniqueId}
                          className={`${styles.cinemaCard} ${isThisCinemaSelected ? styles.selected : ''}`}
                        >
                          <div 
                            className={styles.cinemaInfo}
                            onClick={() => handleCinemaSelect(cinema.uniqueId)}
                          >
                            <div className={styles.cinemaHeader}>
                              <h4>{cinema.name}</h4>
                              <div className={styles.radio}>
                                {isThisCinemaSelected && (
                                  <div className={styles.radioActive}></div>
                                )}
                              </div>
                            </div>
                            <p className={styles.cinemaAddress}>
                              {cinema.address}, {cinema.district}
                            </p>
                          </div>

                          {isThisCinemaSelected && (
                            <div className={styles.showtimeSection}>
                              <p className={styles.showtimeLabel}>Chọn giờ chiếu:</p>
                              <div className={styles.showtimeGrid}>
                                {SHOWTIMES.map((time) => (
                                  <button
                                    key={time}
                                    className={`${styles.showtimeBtn} ${selectedShowtime === time ? styles.selected : ''}`}
                                    onClick={(e) => handleShowtimeSelect(time, e)}
                                  >
                                    {time}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {step === 'cinema' && (
          <div className={styles.footer}>
            <button 
              className={styles.confirmBtn}
              onClick={handleConfirm}
              disabled={!selectedCinema || !selectedShowtime || !selectedDate}
            >
              Xác nhận đặt vé
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
