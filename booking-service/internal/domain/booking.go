package domain

import "time"

type BookingStatus string

const (
	BookingStatusPending   BookingStatus = "PENDING"
	BookingStatusConfirmed BookingStatus = "CONFIRMED"
	BookingStatusCancelled BookingStatus = "CANCELLED"
	BookingStatusFailed    BookingStatus = "FAILED"
)

type Booking struct {
	ID         string   `json:"id"`
	UserID     int      `json:"user_id"`
	ShowtimeID string   `json:"showtime_id"`
	SeatIDs    []int    `json:"seat_ids"`
	Tickets    []Ticket `json:"tickets"`

	FoodItems  []BookingFoodItem `json:"food_items"` // Optional food/beverage items
	TotalPrice float64           `json:"total_price"`
	Status     BookingStatus     `json:"status"`
	CreatedAt  time.Time         `json:"created_at"`
	ExpiresAt  time.Time         `json:"expires_at"`
}

type PaymentWebhookRequest struct {
	BookingID     string `json:"booking_id"`
	PaymentStatus string `json:"payment_status"` // "SUCCESS" or "FAILED"
	TransactionID string `json:"transaction_id"`
}
