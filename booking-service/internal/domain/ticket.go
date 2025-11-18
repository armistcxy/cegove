package domain

import "time"

type TicketStatus int

const (
	TicketStatusActive TicketStatus = iota
	TicketStatusUsed
	TicketStatusCancelled
)

type Ticket struct {
	ID         string `json:"id"`
	BookingID  string `json:"booking_id"`
	ShowtimeID string `json:"showtime_id"`

	MovieTitle string    `json:"movie_title"`
	CinemaName string    `json:"cinema_name"`
	ScreenName string    `json:"screen_name"`
	Showtime   time.Time `json:"showtime"`
	SeatRow    string    `json:"seat_row"`
	SeatNumber int       `json:"seat_number"`

	QRCode    string       `json:"qr_code"`
	Price     float64      `json:"price"`
	Status    TicketStatus `json:"status"`
	CreatedAt time.Time    `json:"created_at"`
}
