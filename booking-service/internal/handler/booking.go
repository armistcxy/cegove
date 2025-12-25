package handler

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/internal/repository"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/spf13/cast"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/baggage"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/trace"
)

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
	logger           *logging.Logger
	bookingRepo      repository.BookingRepository
	userRepo         repository.UserRepository
	foodRepo         repository.FoodRepository
	requestsTotal    prometheus.Counter
	requestsDuration prometheus.Histogram
}

func NewBookingHandler(bookingRepo repository.BookingRepository, userRepo repository.UserRepository, foodRepo repository.FoodRepository, logger *logging.Logger, reg prometheus.Registerer) *BookingHandler {
	requestsTotal := prometheus.NewCounter(prometheus.CounterOpts{
		Name: "booking_requests_total",
		Help: "Total number of booking requests",
	})

	requestsDuration := prometheus.NewHistogram(prometheus.HistogramOpts{
		Name: "booking_request_duration_seconds",
		Help: "Duration of booking requests in seconds",
	})

	if reg != nil {
		reg.MustRegister(requestsTotal, requestsDuration)
	} else {
		prometheus.MustRegister(requestsTotal, requestsDuration)
	}

	return &BookingHandler{
		logger:           logger,
		bookingRepo:      bookingRepo,
		userRepo:         userRepo,
		foodRepo:         foodRepo,
		requestsTotal:    requestsTotal,
		requestsDuration: requestsDuration,
	}
}

type createBookingRequest struct {
	UserID     string                     `json:"user_id" example:"user123"`
	ShowtimeID string                     `json:"showtime_id" example:"showtime123"`
	SeatIDs    []string                   `json:"seat_ids" example:"seat1,seat2"`
	FoodItems  []createBookingFoodRequest `json:"food_items,omitempty"` // Optional food/beverage items
}

type createBookingFoodRequest struct {
	FoodItemID string `json:"food_item_id" example:"food123"`
	Quantity   int    `json:"quantity" example:"2"`
}

func (h *BookingHandler) recordMetrics() func() {
	timer := prometheus.NewTimer(h.requestsDuration)
	return func() {
		h.requestsTotal.Inc()
		timer.ObserveDuration()
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
	defer h.recordMetrics()()

	ctx := r.Context()

	// Decode request payload
	req, err := httphelp.DecodeJSON[createBookingRequest](r)
	if err != nil {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
		return
	}

	// Build booking domain object
	seatID := make([]int, 0, len(req.SeatIDs))
	for _, s := range req.SeatIDs {
		seatID = append(seatID, cast.ToInt(s))
	}
	booking := domain.Booking{
		UserID:     cast.ToInt(req.UserID),
		ShowtimeID: req.ShowtimeID,
		SeatIDs:    seatID,
		Status:     domain.BookingStatusPending,
	}

	// Process optional food items
	if len(req.FoodItems) > 0 {
		foodItems := make([]domain.BookingFoodItem, 0, len(req.FoodItems))
		for _, f := range req.FoodItems {
			foodItem, err := h.foodRepo.GetFoodItem(ctx, f.FoodItemID)
			if err != nil {
				h.logger.Error("Failed to get food item", err)
				httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
				return
			}
			if !foodItem.Available {
				httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("food item not available"))
				return
			}
			bookingFood := domain.BookingFoodItem{
				FoodItemID: foodItem.ID,
				Quantity:   f.Quantity,
				Price:      foodItem.Price,
			}
			foodItems = append(foodItems, bookingFood)
		}
		booking.FoodItems = foodItems
	}

	// Execute booking insertion
	if err := h.bookingRepo.InsertBooking(ctx, &booking); err != nil {
		h.logger.Error("Failed to create booking", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	// Create span with booking ID and set as trace ID
	tracer := otel.Tracer("booking-service")
	spanCtx, span := tracer.Start(ctx, "CreateBooking",
		trace.WithAttributes(
			attribute.String("booking.id", booking.ID),
			attribute.String("user.id", cast.ToString(booking.UserID)),
			attribute.String("showtime.id", booking.ShowtimeID),
		),
	)
	defer span.End()

	paymentURL := "https://payment.cegove.cloud/api/v1/payments/"
	paymentPayload := map[string]any{
		"booking_id": booking.ID,
		"amount":     booking.TotalPrice,
		"provider":   "vnpay",
		"client_ip":  r.RemoteAddr,
	}
	paymentPayloadBytes, err := json.Marshal(paymentPayload)
	if err != nil {
		h.logger.Error("Failed to marshal payment payload", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	paymentReq, err := http.NewRequestWithContext(spanCtx, "POST", paymentURL, bytes.NewReader(paymentPayloadBytes))
	if err != nil {
		h.logger.Error("Failed to create payment request", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	paymentReq.Header.Set("Content-Type", "application/json")

	// Inject trace context into the payment request headers
	otel.GetTextMapPropagator().Inject(spanCtx, propagation.HeaderCarrier(paymentReq.Header))

	client := http.Client{
		Transport: otelhttp.NewTransport(http.DefaultTransport),
	}

	paymentResp, err := client.Do(paymentReq)
	if err != nil {
		h.logger.Error("Failed to send payment request", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	var paymentResponse struct {
		Payment struct {
			ID     int    `json:"id"`
			Amount string `json:"amount"`
		} `json:"payment"`
		URL string `json:"url"`
	}
	if err := json.NewDecoder(paymentResp.Body).Decode(&paymentResponse); err != nil {
		h.logger.Error("Failed to decode payment response", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	// Respond with full booking including tickets
	httphelp.EncodeJSON(w, r, http.StatusOK, map[string]any{
		"booking": booking,
		"payment": paymentResponse,
	})
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
	defer h.recordMetrics()()

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
	defer h.recordMetrics()()

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
	defer h.recordMetrics()()

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

	// Create span with booking ID
	tracer := otel.Tracer("booking-service")
	spanCtx, span := tracer.Start(ctx, "ProcessPaymentWebhook",
		trace.WithAttributes(
			attribute.String("booking.id", req.BookingID),
			attribute.String("payment.status", req.PaymentStatus),
		),
	)
	defer span.End()

	// Process payment status update
	err = h.bookingRepo.ProcessPaymentWebhook(spanCtx, req)
	if err != nil {
		h.logger.Error("Failed to process payment webhook", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	if req.PaymentStatus == "SUCCESS" {
		// get booking information
		booking, err := h.bookingRepo.GetBookingInformation(spanCtx, req.BookingID)
		if err != nil {
			h.logger.Error("Failed to get booking information", err)
			httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
			return
		}
		h.logger.Info("Booking information", "booking", booking)

		// get user email
		email, err := h.userRepo.GetUserEmail(spanCtx, cast.ToString(booking.UserID))
		if err != nil {
			h.logger.Error("Failed to get user email", err)
			httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
			return
		}
		h.logger.Info("User email", "email", email)

		// Create a copy of booking with cleared QR codes before sending email
		bookingForEmail := *booking
		for i := range bookingForEmail.Tickets {
			bookingForEmail.Tickets[i].QRCode = ""
		}

		notificationURL := "https://notification.cegove.cloud/v1/notifications/send"
		notificationPayload := map[string]any{
			"to":      []string{email},
			"subject": "Booking Confirmation",
			"body":    GenerateBookingConfirmationEmail(&bookingForEmail, email),
		}
		notificationPayloadBytes, err := json.Marshal(notificationPayload)
		if err != nil {
			h.logger.Error("Failed to marshal notification payload", err)
			httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
			return
		}
		notificationReq, err := http.NewRequestWithContext(spanCtx, "POST", notificationURL, bytes.NewReader(notificationPayloadBytes))
		if err != nil {
			h.logger.Error("Failed to create notification request", err)
			httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
			return
		}
		notificationReq.Header.Set("Content-Type", "application/json")

		// Add booking.id to baggage so it can be extracted by notification service
		bag, _ := baggage.Parse("")
		member, _ := baggage.NewMember("booking.id", req.BookingID)
		bag, _ = bag.SetMember(member)
		bagCtx := baggage.ContextWithBaggage(spanCtx, bag)

		// Inject trace context and baggage into the notification request headers
		otel.GetTextMapPropagator().Inject(bagCtx, propagation.HeaderCarrier(notificationReq.Header))

		client := http.Client{
			Transport: otelhttp.NewTransport(http.DefaultTransport),
		}

		notificationResp, err := client.Do(notificationReq)
		if err != nil {
			h.logger.Error("Failed to send notification request", err)
			httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
			return
		}
		if notificationResp != nil {
			defer notificationResp.Body.Close()
		}
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
	defer h.recordMetrics()()

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
