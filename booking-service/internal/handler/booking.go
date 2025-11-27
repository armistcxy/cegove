package handler

import (
	"errors"
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/internal/repository"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
)

type createBookingRequest struct {
	UserID     string   `json:"user_id" example:"user123"`
	ShowtimeID string   `json:"showtime_id" example:"showtime123"`
	SeatIDs    []string `json:"seat_ids" example:"seat1,seat2"`
}

// @BasePath /api/v1

// @Summary Create a new booking
// @Description Create a new booking for a user and showtime with selected seats
// @Tags bookings
// @Accept json
// @Produce json
// @Param booking body createBookingRequest true "Booking creation request"
// @Success 200 {object} domain.Booking "Booking created successfully"
// @Router /bookings [post]

type BookingHandle struct {
	logger      *logging.Logger
	bookingRepo repository.BookingRepository
}

func NewBookingHandler(bookingRepo repository.BookingRepository, logger *logging.Logger) *BookingHandle {
	return &BookingHandle{
		logger:      logger,
		bookingRepo: bookingRepo,
	}
}

// @Summary Create a new booking
// @Description Create a new booking for a user and showtime with selected seats
// @Tags bookings
// @Accept json
// @Produce json
// @Param booking body createBookingRequest true "Booking creation request"
// @Success 200 {object} domain.Booking "Booking created successfully"
// @Router /bookings [post]
func (h *BookingHandle) HandleCreateBooking(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Decode request payload
	req, err := httphelp.DecodeJSON[createBookingRequest](r)
	if err != nil {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
		return
	}

	// Build booking domain object
	booking := domain.Booking{
		UserID:     req.UserID,
		ShowtimeID: req.ShowtimeID,
		SeatIDs:    req.SeatIDs,
	}

	// Execute booking insertion
	if err := h.bookingRepo.InsertBooking(ctx, &booking); err != nil {
		h.logger.Error("Failed to create booking", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	// Respond with full booking including tickets
	httphelp.EncodeJSON(w, r, http.StatusOK, booking)
}

// @Summary Get booking information
// @Description Get detailed information about a specific booking
// @Tags bookings
// @Produce json
// @Param booking_id path string true "Booking ID"
// @Success 200 {object} domain.Booking "Booking information retrieved successfully"
// @Router /bookings/{booking_id} [get]
// @Summary Get booking information
// @Description Get detailed information about a specific booking
// @Tags bookings
// @Produce json
// @Param booking_id path string true "Booking ID"
// @Success 200 {object} domain.Booking "Booking information retrieved successfully"
// @Router /bookings/{booking_id} [get]
func (h *BookingHandle) HandleGetBookingInformation(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	bookingID := r.PathValue("booking_id")
	if bookingID == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("missing booking ID"))
		return
	}

	booking, err := h.bookingRepo.GetBookingInformation(ctx, bookingID)
	if err != nil {
		h.logger.Error("Failed to get booking information", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, booking)
}

// @Summary List all bookings
// @Description Get a list of all bookings
// @Tags bookings
// @Produce json
// @Success 200 {array} domain.Booking "List of bookings retrieved successfully"
// @Router /bookings [get]
// @Summary List all bookings
// @Description Get a list of all bookings
// @Tags bookings
// @Produce json
// @Success 200 {array} domain.Booking "List of bookings retrieved successfully"
// @Router /bookings [get]
func (h *BookingHandle) HandleListBookings(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	bookings, err := h.bookingRepo.ListBookings(ctx)
	if err != nil {
		h.logger.Error("Failed to list bookings", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, bookings)
}
