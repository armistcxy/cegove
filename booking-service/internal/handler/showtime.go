package handler

import (
	"errors"
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/internal/repository"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
)

type ShowtimeHandler struct {
	logger       *logging.Logger
	showtimeRepo repository.ShowtimeRepository
}

func NewShowtimeHandler(showtimeRepo repository.ShowtimeRepository, logger *logging.Logger) *ShowtimeHandler {
	return &ShowtimeHandler{
		logger:       logger,
		showtimeRepo: showtimeRepo,
	}
}

// @Summary List all showtimes
// @Description Get a list of all available showtimes
// @Tags showtimes
// @Produce json
// @Success 200 {array} domain.Showtime "List of showtimes retrieved successfully"
// @Router /showtimes [get]
func (h *ShowtimeHandler) HandleListShowtimes(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	// optional query params to filter
	q := r.URL.Query()
	movieID := q.Get("movie_id")
	cinemaID := q.Get("cinema_id")

	showtimes, err := h.showtimeRepo.ListShowtimes(ctx, movieID, cinemaID)
	if err != nil {
		h.logger.Error("Failed to list showtimes", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	httphelp.EncodeJSON(w, r, http.StatusOK, showtimes)
}

// @Summary Get showtime seats
// @Description Get a list of seats for a specific showtime
// @Tags showtimes
// @Produce json
// @Param showtime_id path string true "Showtime ID"
// @Success 200 {array} domain.ShowtimeSeat "List of showtime seats retrieved successfully"
// @Router /showtimes/{showtime_id}/seats [get]
func (h *ShowtimeHandler) HandleGetShowtimeSeats(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	showtimeID := r.PathValue("showtime_id")
	if showtimeID == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("missing showtime ID"))
		return
	}
	seats, err := h.showtimeRepo.GetShowtimeSeats(ctx, showtimeID)
	if err != nil {
		h.logger.Error("Failed to get showtime seats", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	httphelp.EncodeJSON(w, r, http.StatusOK, seats)
}

// @Summary Get showtime seats V2 (Rich Data)
// @Description Get seats with computed labels and visual metadata suitable for frontend rendering
// @Tags showtimes
// @Produce json
// @Param showtime_id path string true "Showtime ID"
// @Success 200 {array} domain.SeatV2Response
// @Router /v2/showtimes/{showtime_id}/seats [get]
func (h *ShowtimeHandler) HandleGetShowtimeSeatsV2(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	showtimeID := r.PathValue("showtime_id")
	if showtimeID == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("missing showtime ID"))
		return
	}

	rawSeats, err := h.showtimeRepo.GetShowtimeSeats(ctx, showtimeID)
	if err != nil {
		h.logger.Error("Failed to get showtime seats", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	v2Response := make([]domain.SeatV2Response, 0, len(rawSeats))

	for i, s := range rawSeats {
		mockRow := "A"
		if i > 5 {
			mockRow = "B"
		}
		mockNum := (i % 6) + 1
		mockType := domain.SeatTypeNormal
		if mockRow == "B" {
			mockType = domain.SeatTypeVIP
		}

		v2Seat := domain.MapShowtimeSeatToV2(s, mockRow, mockNum, mockType)
		v2Response = append(v2Response, v2Seat)
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, v2Response)
}
