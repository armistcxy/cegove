package handler

import (
	"errors"
	"net/http"
	"time"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/internal/repository"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
	"github.com/google/uuid"
	"golang.org/x/sync/errgroup"
)

type ShowtimeHandler struct {
	logger       *logging.Logger
	showtimeRepo repository.ShowtimeRepository
	seatRepo     repository.SeatRepository
}

func NewShowtimeHandler(showtimeRepo repository.ShowtimeRepository, seatRepo repository.SeatRepository, logger *logging.Logger) *ShowtimeHandler {
	return &ShowtimeHandler{
		logger:       logger,
		showtimeRepo: showtimeRepo,
		seatRepo:     seatRepo,
	}
}

func (h *ShowtimeHandler) HandleGetShowtime(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	showtimeID := r.PathValue("showtime_id")
	if showtimeID == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("missing showtime ID"))
		return
	}
	showtime, err := h.showtimeRepo.GetShowtime(ctx, showtimeID)
	if err != nil {
		h.logger.Error("Failed to get showtime", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}
	httphelp.EncodeJSON(w, r, http.StatusOK, showtime)
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

	var date = time.Now()
	dateStr := q.Get("date")
	if dateStr != "" {
		var err error
		date, err = time.Parse("2006-01-02", dateStr)
		if err != nil {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
			return
		}
	}

	showtimes, err := h.showtimeRepo.ListShowtimes(ctx, movieID, cinemaID, date)
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

type CreateShowtimesRequest struct {
	Showtimes []domain.Showtime `json:"showtimes"`
}

// @Summary Create showtimes
// @Description Create showtimes
// @Tags showtimes
// @Produce json
// @Param showtimes body CreateShowtimesRequest true "Showtimes creation request"
// @Success 200 {object} map[string]string "Showtimes created successfully"
// @Router /showtimes [post]
func (h *ShowtimeHandler) HandleCreateShowtimes(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	req, err := httphelp.DecodeJSON[CreateShowtimesRequest](r)
	if err != nil {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, err)
		return
	}

	if len(req.Showtimes) == 0 {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("no showtimes provided"))
		return
	}

	for i := range req.Showtimes {
		req.Showtimes[i].ID = uuid.New().String()
		if req.Showtimes[i].StartTime.IsZero() {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("start time is required"))
			return
		}
		if req.Showtimes[i].EndTime.IsZero() {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("end time is required"))
			return
		}
		if req.Showtimes[i].BasePrice <= 0 {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("base price must be greater than 0"))
			return
		}
		if req.Showtimes[i].EndTime.Before(req.Showtimes[i].StartTime) {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("end time must be after start time"))
			return
		}
		if req.Showtimes[i].MovieID == "" {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("movie ID is required"))
			return
		}
		if req.Showtimes[i].AuditoriumID == "" {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("auditorium ID is required"))
			return
		}
		if req.Showtimes[i].CinemaID == "" {
			httphelp.EncodeJSONError(w, r, http.StatusBadRequest, errors.New("cinema ID is required"))
			return
		}
	}

	err = h.showtimeRepo.InsertShowtimes(ctx, req.Showtimes)
	if err != nil {
		h.logger.Error("Failed to insert showtimes", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	var errGroup errgroup.Group
	for _, st := range req.Showtimes {
		st := st
		errGroup.Go(func() error {
			seats, err := h.seatRepo.ListSeats(ctx, st.AuditoriumID)
			if err != nil {
				h.logger.Error("Failed to list seats", err)
				httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
				return nil
			}

			showtimeSeats := make([]domain.ShowtimeSeat, len(seats))
			for i, s := range seats {
				multiplier := 1.0
				if s.Type == "VIP" {
					multiplier = 1.5
				}
				if s.Type == "COUPLE" {
					multiplier = 3.5
				}
				showtimeSeats[i] = domain.ShowtimeSeat{
					SeatID:     s.ID,
					ShowtimeID: st.ID,
					Status:     domain.SeatStatusAvailable,
					Price:      st.BasePrice * multiplier,
				}
			}
			return h.showtimeRepo.InsertShowtimeSeats(ctx, st.ID, showtimeSeats)
		})
	}
	if err := errGroup.Wait(); err != nil {
		h.logger.Error("Failed to insert showtime seats", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	showtimeIDs := make([]string, len(req.Showtimes))
	for i, st := range req.Showtimes {
		showtimeIDs[i] = st.ID
	}
	httphelp.EncodeJSON(w, r, http.StatusOK, map[string][]string{"showtime_ids": showtimeIDs})
}
