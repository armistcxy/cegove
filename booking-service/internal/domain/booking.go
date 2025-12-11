package domain

import "time"

type BookingStatus int

const (
	BookingStatusPending BookingStatus = iota
	BookingStatusConfirmed
	BookingStatusCancelled
	BookingStatusFailed
)

type Booking struct {
	ID         string   `json:"id"`
	UserID     string   `json:"user_id"`
	ShowtimeID string   `json:"showtime_id"`
	SeatIDs    []string `json:"seat_ids"`
	Tickets    []Ticket `json:"tickets"`

	TotalPrice float64       `json:"total_price"`
	Status     BookingStatus `json:"status"`
	CreatedAt  time.Time     `json:"created_at"`
	ExpiresAt  time.Time     `json:"expires_at"`
}

type PaymentWebhookRequest struct {
	BookingID     string `json:"booking_id"`
	PaymentStatus string `json:"payment_status"` // "SUCCESS" or "FAILED"
	TransactionID string `json:"transaction_id"`
}
