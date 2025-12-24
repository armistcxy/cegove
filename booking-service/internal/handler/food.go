package handler

import (
	"net/http"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
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

// @Summary List food items by type
// @Description Get food items filtered by type (POPCORN, DRINK, COMBO)
// @Tags food
// @Produce json
// @Param type query string false "Food type (POPCORN, DRINK, COMBO)"
// @Success 200 {array} domain.FoodItem "Filtered food items"
// @Failure 500 {object} map[string]string "Internal error"
// @Router /food/items/by-type [get]
func (h *FoodHandler) HandleListFoodItemsByType(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	foodType := domain.FoodType(r.URL.Query().Get("type"))
	if foodType == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, nil)
		return
	}

	foodItems, err := h.foodRepo.ListFoodItemsByType(ctx, foodType)
	if err != nil {
		h.logger.Error("Failed to list food items by type", err)
		httphelp.EncodeJSONError(w, r, http.StatusInternalServerError, err)
		return
	}

	httphelp.EncodeJSON(w, r, http.StatusOK, foodItems)
}

// @Summary List food items by category
// @Description Get food items filtered by category (SNACKS, BEVERAGES, BUNDLE)
// @Tags food
// @Produce json
// @Param category query string false "Food category (SNACKS, BEVERAGES, BUNDLE)"
// @Success 200 {array} domain.FoodItem "Filtered food items"
// @Failure 500 {object} map[string]string "Internal error"
// @Router /food/items/by-category [get]
func (h *FoodHandler) HandleListFoodItemsByCategory(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	category := domain.FoodCategory(r.URL.Query().Get("category"))
	if category == "" {
		httphelp.EncodeJSONError(w, r, http.StatusBadRequest, nil)
		return
	}

	foodItems, err := h.foodRepo.ListFoodItemsByCategory(ctx, category)
	if err != nil {
		h.logger.Error("Failed to list food items by category", err)
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
