package domain

type SeatType int

const (
	SeatTypeNormal SeatType = iota
	SeatTypeVIP
	SeatTypeCouple
)

type SeatStatus int

const (
	SeatStatusAvailable SeatStatus = iota
	SeatStatusLocked
	SeatStatusSold
)

type Seat struct {
	ID     string `json:"id"`
	Row    string `json:"row"`    // Name of row, could be "A", "B", "C", etc.
	Number int    `json:"number"` // Number of seat in row, could be 1, 2, 3, etc.

	Type     SeatType `json:"type"`
	ScreenID string   `json:"screen_id"` // ID of the
}

type ShowtimeSeat struct {
	SeatID     string     `json:"seat_id"`
	ShowtimeID string     `json:"showtime_id"`
	Status     SeatStatus `json:"status"`
	Price      float64    `json:"price"`
	BookingID  string     `json:"booking_id,omitempty"`
}
