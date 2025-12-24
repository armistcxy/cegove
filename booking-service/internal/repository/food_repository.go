package repository

import (
	"context"
	"fmt"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
	"github.com/jackc/pgx/v5/pgxpool"

	sq "github.com/Masterminds/squirrel"
)

type FoodRepository interface {
	GetFoodItem(ctx context.Context, foodItemID string) (*domain.FoodItem, error)
	ListFoodItems(ctx context.Context) ([]domain.FoodItem, error)
	ListFoodItemsByType(ctx context.Context, foodType domain.FoodType) ([]domain.FoodItem, error)
	ListFoodItemsByCategory(ctx context.Context, category domain.FoodCategory) ([]domain.FoodItem, error)
}

type foodRepository struct {
	pool   *pgxpool.Pool
	logger *logging.Logger
}

func NewFoodRepository(pool *pgxpool.Pool, logger *logging.Logger) FoodRepository {
	return &foodRepository{
		pool:   pool,
		logger: logger,
	}
}

func (r *foodRepository) GetFoodItem(ctx context.Context, foodItemID string) (*domain.FoodItem, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	query, args, err := builder.Select(
		"id", "name", "type", "category", "price", "image_url", "available", "created_at",
	).From("food_items").
		Where(sq.Eq{"id": foodItemID}).
		ToSql()
	if err != nil {
		return nil, fmt.Errorf("build query: %w", err)
	}

	var foodItem domain.FoodItem
	if err := r.pool.QueryRow(ctx, query, args...).Scan(
		&foodItem.ID,
		&foodItem.Name,
		&foodItem.Type,
		&foodItem.Category,
		&foodItem.Price,
		&foodItem.ImageURL,
		&foodItem.Available,
		&foodItem.CreatedAt,
	); err != nil {
		return nil, fmt.Errorf("query food item: %w", err)
	}

	return &foodItem, nil
}

func (r *foodRepository) ListFoodItems(ctx context.Context) ([]domain.FoodItem, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	query, args, err := builder.Select(
		"id", "name", "type", "category", "price", "image_url", "available", "created_at",
	).From("food_items").
		Where(sq.Eq{"available": true}).
		OrderBy("category", "name").
		ToSql()
	if err != nil {
		return nil, fmt.Errorf("build query: %w", err)
	}

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query food items: %w", err)
	}
	defer rows.Close()

	foodItems := make([]domain.FoodItem, 0)
	for rows.Next() {
		var foodItem domain.FoodItem
		if err := rows.Scan(
			&foodItem.ID,
			&foodItem.Name,
			&foodItem.Type,
			&foodItem.Category,
			&foodItem.Price,
			&foodItem.ImageURL,
			&foodItem.Available,
			&foodItem.CreatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan food item: %w", err)
		}
		foodItems = append(foodItems, foodItem)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}

	return foodItems, nil
}

func (r *foodRepository) ListFoodItemsByType(ctx context.Context, foodType domain.FoodType) ([]domain.FoodItem, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	query, args, err := builder.Select(
		"id", "name", "type", "category", "price", "image_url", "available", "created_at",
	).From("food_items").
		Where(sq.Eq{"type": foodType}).
		Where(sq.Eq{"available": true}).
		OrderBy("name").
		ToSql()
	if err != nil {
		return nil, fmt.Errorf("build query: %w", err)
	}

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query food items: %w", err)
	}
	defer rows.Close()

	foodItems := make([]domain.FoodItem, 0)
	for rows.Next() {
		var foodItem domain.FoodItem
		if err := rows.Scan(
			&foodItem.ID,
			&foodItem.Name,
			&foodItem.Type,
			&foodItem.Category,
			&foodItem.Price,
			&foodItem.ImageURL,
			&foodItem.Available,
			&foodItem.CreatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan food item: %w", err)
		}
		foodItems = append(foodItems, foodItem)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}

	return foodItems, nil
}

func (r *foodRepository) ListFoodItemsByCategory(ctx context.Context, category domain.FoodCategory) ([]domain.FoodItem, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	query, args, err := builder.Select(
		"id", "name", "type", "category", "price", "image_url", "available", "created_at",
	).From("food_items").
		Where(sq.Eq{"category": category}).
		Where(sq.Eq{"available": true}).
		OrderBy("name").
		ToSql()
	if err != nil {
		return nil, fmt.Errorf("build query: %w", err)
	}

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query food items: %w", err)
	}
	defer rows.Close()

	foodItems := make([]domain.FoodItem, 0)
	for rows.Next() {
		var foodItem domain.FoodItem
		if err := rows.Scan(
			&foodItem.ID,
			&foodItem.Name,
			&foodItem.Type,
			&foodItem.Category,
			&foodItem.Price,
			&foodItem.ImageURL,
			&foodItem.Available,
			&foodItem.CreatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan food item: %w", err)
		}
		foodItems = append(foodItems, foodItem)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}

	return foodItems, nil
}
