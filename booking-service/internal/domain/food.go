package domain

import "time"

type FoodType string

const (
	FoodTypePopcorn FoodType = "POPCORN"
	FoodTypeDrink   FoodType = "DRINK"
	FoodTypeCombo   FoodType = "COMBO"
)

type FoodCategory string

const (
	FoodCategorySnacks    FoodCategory = "SNACKS"
	FoodCategoryBeverages FoodCategory = "BEVERAGES"
	FoodCategoryBundle    FoodCategory = "BUNDLE"
)

// FoodItem represents a food/beverage product available for booking
type FoodItem struct {
	ID        string       `json:"id"`
	Name      string       `json:"name"`
	Type      FoodType     `json:"type"`
	Category  FoodCategory `json:"category"`
	Price     float64      `json:"price"`
	ImageURL  string       `json:"image_url"`
	Available bool         `json:"available"`
	CreatedAt time.Time    `json:"created_at"`
}

// BookingFoodItem represents a food item selected in a booking
type BookingFoodItem struct {
	FoodItemID string  `json:"food_item_id"`
	Quantity   int     `json:"quantity"`
	Price      float64 `json:"price"` // Price at time of booking
}
