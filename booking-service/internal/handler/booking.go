package handler

import (
	"booking-service/internal/domain"
	"booking-service/internal/repository"
	"booking-service/pkg/httphelp"
	"booking-service/pkg/logging"
	"errors"
	"net/http"
)

type createBookingRequest struct {
	UserID     string   `json:"user_id"`
	ShowtimeID string   `json:"showtime_id"`
	SeatIDs    []string `json:"seat_ids"`
}

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
