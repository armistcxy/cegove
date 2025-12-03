package domain

import (
	"fmt"
	"time"
)

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
	ScreenID string   `json:"screen_id"` // ID of the screen
}

type ShowtimeSeat struct {
	SeatID     string     `json:"seat_id"`
	ShowtimeID string     `json:"showtime_id"`
	Status     SeatStatus `json:"status"`
	Price      float64    `json:"price"`
	BookingID  string     `json:"booking_id,omitempty"`
}

type Showtime struct {
	ID        string    `json:"id"`
	MovieID   string    `json:"movie_id"`
	CinemaID  string    `json:"cinema_id"`
	ScreenID  string    `json:"screen_id"`
	StartTime time.Time `json:"start_time"`
	EndTime   time.Time `json:"end_time"`
	BasePrice float64   `json:"base_price"`
	Status    int       `json:"status"`
}

type SeatV2Response struct {
	ID         string       `json:"id"`
	Label      string       `json:"label"`
	StatusText string       `json:"status_text"`
	Position   SeatPosition `json:"position"`
	Metadata   SeatMetadata `json:"metadata"`
	Pricing    SeatPricing  `json:"pricing"`
}

type SeatPosition struct {
	Row    string `json:"row"`
	Number int    `json:"number"`
	GridX  int    `json:"grid_x"`
	GridY  int    `json:"grid_y"`
}

type SeatMetadata struct {
	TypeCode    string `json:"type_code"`
	DisplayName string `json:"display_name"`
	ColorHex    string `json:"color_hex"`
}

type SeatPricing struct {
	Amount   float64 `json:"amount"`
	Currency string  `json:"currency"`
}

func MapShowtimeSeatToV2(s ShowtimeSeat, seatRow string, seatNum int, seatType SeatType) SeatV2Response {
	label := fmt.Sprintf("%s-%02d", seatRow, seatNum)

	var statusText string
	switch s.Status {
	case SeatStatusAvailable:
		statusText = "Available"
	case SeatStatusLocked:
		statusText = "Reserved"
	case SeatStatusSold:
		statusText = "Sold"
	default:
		statusText = "Unknown"
	}

	var meta SeatMetadata
	switch seatType {
	case SeatTypeVIP:
		meta = SeatMetadata{TypeCode: "VIP", DisplayName: "Ghế VIP (Premium)", ColorHex: "#FFD700"} // Vàng
	case SeatTypeCouple:
		meta = SeatMetadata{TypeCode: "COUPLE", DisplayName: "Ghế Đôi (Sweetbox)", ColorHex: "#FF69B4"} // Hồng
	default:
		meta = SeatMetadata{TypeCode: "NORMAL", DisplayName: "Ghế Tiêu Chuẩn", ColorHex: "#CCCCCC"} // Xám
	}

	rowIndex := int(seatRow[0]) - int('A') + 1

	return SeatV2Response{
		ID:         s.SeatID,
		Label:      label,
		StatusText: statusText,
		Position: SeatPosition{
			Row:    seatRow,
			Number: seatNum,
			GridX:  seatNum,
			GridY:  rowIndex,
		},
		Metadata: meta,
		Pricing: SeatPricing{
			Amount:   s.Price,
			Currency: "VND",
		},
	}
}
