package repository

import (
	"context"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/jackc/pgx/v5/pgxpool"
)

type SeatRepository interface {
	ListSeats(ctx context.Context, auditoriumID string) ([]domain.Seat, error)
}

type seatRepository struct {
	pool *pgxpool.Pool
}

func NewSeatRepository(pool *pgxpool.Pool) SeatRepository {
	return &seatRepository{
		pool: pool,
	}
}

func (r *seatRepository) ListSeats(ctx context.Context, auditoriumID string) ([]domain.Seat, error) {
	query := `
		SELECT id, seat_number, seat_type
		FROM seats
		WHERE auditorium_id = $1
	`

	rows, err := r.pool.Query(ctx, query, auditoriumID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	seats := make([]domain.Seat, 0)
	for rows.Next() {
		var s domain.Seat
		if err := rows.Scan(&s.ID, &s.Number, &s.Type); err != nil {
			return nil, err
		}
		seats = append(seats, s)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return seats, nil
}
