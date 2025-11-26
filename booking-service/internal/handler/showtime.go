package handler

import (
	"booking-service/internal/repository"
	"booking-service/pkg/httphelp"
	"booking-service/pkg/logging"
	"errors"
	"net/http"
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

func (h *ShowtimeHandler) HandleListShowtimes(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	showtimes, err := h.showtimeRepo.ListShowtimes(ctx)
	if err != nil {
		h.logger.Error("Failed to list showtimes", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	httphelp.EncodeJSON(w, r, http.StatusOK, showtimes)
}

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
