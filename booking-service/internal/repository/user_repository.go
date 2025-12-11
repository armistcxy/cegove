package repository

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

type UserRepository interface {
	GetUserEmail(ctx context.Context, userID string) (string, error)
}

type userRepository struct {
	pool *pgxpool.Pool
}

func NewUserRepository(pool *pgxpool.Pool) UserRepository {
	return &userRepository{
		pool: pool,
	}
}

func (r *userRepository) GetUserEmail(ctx context.Context, userID string) (string, error) {
	query := "SELECT email FROM users WHERE id = $1"
	row := r.pool.QueryRow(ctx, query, userID)
	var email string
	err := row.Scan(&email)
	if err != nil {
		return "", err
	}
	return email, nil
}
