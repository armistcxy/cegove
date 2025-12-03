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
type BookingHandler struct {
	logger      *logging.Logger
	bookingRepo repository.BookingRepository
}

func NewBookingHandler(bookingRepo repository.BookingRepository, logger *logging.Logger) *BookingHandler {
	return &BookingHandler{
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
func (h *BookingHandler) HandleCreateBooking(w http.ResponseWriter, r *http.Request) {
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
func (h *BookingHandler) HandleGetBookingInformation(w http.ResponseWriter, r *http.Request) {
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
func (h *BookingHandler) HandleListBookings(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	bookings, err := h.bookingRepo.ListBookings(ctx)
	if err != nil {
		h.logger.Error("Failed to list bookings", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, bookings)
}

// @Summary Handle Payment Webhook
// @Description Receive payment status updates from Payment Service
// @Tags bookings
// @Accept json
// @Produce json
// @Param payment body domain.PaymentWebhookRequest true "Payment Status"
// @Success 200 {object} map[string]string "status: received"
// @Failure 400 {object} map[string]string "Invalid payload"
// @Failure 500 {object} map[string]string "Internal Error"
// @Router /bookings/webhooks/payment [post]
func (h *BookingHandler) HandlePaymentWebhook(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	req, err := httphelp.DecodeJSON[domain.PaymentWebhookRequest](r)
	if err != nil {
		h.logger.Error("Failed to decode payment webhook", err)
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
		return
	}

	// Validate required fields
	if req.BookingID == "" || req.PaymentStatus == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("missing required fields"))
		return
	}

	// Process payment status update
	err = h.bookingRepo.ProcessPaymentWebhook(ctx, req)
	if err != nil {
		h.logger.Error("Failed to process payment webhook", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, map[string]string{"status": "received"})
}

type scanTicketRequest struct {
	Code string `json:"code"`
}

// @Summary Scan ticket
// @Description Validate and mark a ticket as used using its QR code
// @Tags tickets
// @Accept json
// @Produce json
// @Param scan body scanTicketRequest true "Scan ticket request"
// @Success 200 {object} domain.Ticket "Ticket scanned successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 404 {object} map[string]string "Ticket not found or already used"
// @Failure 500 {object} map[string]string "Internal error"
// @Router /tickets/scan [post]
func (h *BookingHandler) HandleScanTicket(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	req, err := httphelp.DecodeJSON[scanTicketRequest](r)
	if err != nil {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
		return
	}

	ticket, err := h.bookingRepo.ScanTicket(ctx, req.Code)
	if err != nil {
		h.logger.Error("Failed to scan ticket", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	if ticket == nil {
		httphelp.EncodeJSONError(w, r, http.StatusNotFound, errors.New("ticket not found or already used"))
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, ticket)
}
