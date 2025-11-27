package handler

// @title Booking Service API
// @description This is the API documentation for the Booking Service.
// @version 1.0
// @host localhost:8080
// @BasePath /api/v1

import (
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/repository"

	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"

	"github.com/jackc/pgx/v5/pgxpool"
)

type BookingRouter struct {
	Router *httphelp.Router
}

func NewBookingRouter(pool *pgxpool.Pool, logger *logging.Logger) *BookingRouter {
	router := httphelp.NewRouter()

	bookingRepo := repository.NewBookingRepository(pool)

	bookingHandler := NewBookingHandler(bookingRepo, logger)
	// Showtime routes
	showtimeRepo := repository.NewShowtimeRepository(pool)
	showtimeHandler := NewShowtimeHandler(showtimeRepo, logger)
	router.RegisterHandlerFunc(http.MethodGet, "/showtimes", showtimeHandler.HandleListShowtimes)
	router.RegisterHandlerFunc(http.MethodGet, "/showtimes/{showtime_id}/seats", showtimeHandler.HandleGetShowtimeSeats)

	router.RegisterHandlerFunc(http.MethodPost, "/bookings", bookingHandler.HandleCreateBooking)
	router.RegisterHandlerFunc(http.MethodGet, "/bookings", bookingHandler.HandleListBookings)
	router.RegisterHandlerFunc(http.MethodGet, "/bookings/{booking_id}", bookingHandler.HandleGetBookingInformation)

	return &BookingRouter{
		Router: router,
	}
}
