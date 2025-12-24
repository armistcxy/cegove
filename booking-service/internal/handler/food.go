package handler

import (
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/repository"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
)

type FoodHandler struct {
	logger   *logging.Logger
	foodRepo repository.FoodRepository
}

func NewFoodHandler(foodRepo repository.FoodRepository, logger *logging.Logger) *FoodHandler {
	return &FoodHandler{
		logger:   logger,
		foodRepo: foodRepo,
	}
}

// @Summary List all available food items
// @Description Get a list of all available food items (popcorn, drinks, combos)
// @Tags food
// @Produce json
// @Success 200 {array} domain.FoodItem "List of available food items"
// @Failure 500 {object} map[string]string "Internal error"
// @Router /food/items [get]
func (h *FoodHandler) HandleListFoodItems(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	foodItems, err := h.foodRepo.ListFoodItems(ctx)
	if err != nil {
		h.logger.Error("Failed to list food items", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, foodItems)
}

// @Summary Get food item details
// @Description Get detailed information about a specific food item
// @Tags food
// @Produce json
// @Param food_id path string true "Food Item ID"
// @Success 200 {object} domain.FoodItem "Food item details"
// @Failure 404 {object} map[string]string "Food item not found"
// @Failure 500 {object} map[string]string "Internal error"
// @Router /food/items/{food_id} [get]
func (h *FoodHandler) HandleGetFoodItem(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	foodID := r.PathValue("food_id")
	if foodID == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, nil)
		return
	}

	foodItem, err := h.foodRepo.GetFoodItem(ctx, foodID)
	if err != nil {
		h.logger.Error("Failed to get food item", err)
		httphelp.EncodeJSONError(w, r, http.StatusNotFound, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, foodItem)
}
