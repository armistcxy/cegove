package repository

import (
	"context"
	"fmt"

	"github.com/armistcxy/cegove/booking-service/internal/domain"

	"github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5/pgxpool"
)

type ShowtimeRepository interface {
	ListShowtimes(ctx context.Context) ([]domain.Showtime, error)
	GetShowtimeSeats(ctx context.Context, showtimeID string) ([]domain.ShowtimeSeat, error)
}

type showtimeRepository struct {
	pool         *pgxpool.Pool
	queryBuilder squirrel.StatementBuilderType
}

func NewShowtimeRepository(pool *pgxpool.Pool) ShowtimeRepository {
	return &showtimeRepository{
		pool:         pool,
		queryBuilder: squirrel.StatementBuilder.PlaceholderFormat(squirrel.Dollar),
	}
}

func (r *showtimeRepository) ListShowtimes(ctx context.Context) ([]domain.Showtime, error) {
	builder := r.queryBuilder.Select(
		"id", "movie_id", "screen_id", "start_time", "end_time", "base_price", "status",
	).From("showtimes")
	query, args, err := builder.ToSql()
	if err != nil {
		return nil, fmt.Errorf("build list showtimes query: %w", err)
	}
	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query showtimes: %w", err)
	}
	defer rows.Close()
	showtimes := make([]domain.Showtime, 0)
	for rows.Next() {
		var st domain.Showtime
		if err := rows.Scan(
			&st.ID, &st.MovieID, &st.ScreenID, &st.StartTime, &st.EndTime, &st.BasePrice, &st.Status,
		); err != nil {
			return nil, fmt.Errorf("scan showtime: %w", err)
		}
		showtimes = append(showtimes, st)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}
	return showtimes, nil
}

func (r *showtimeRepository) GetShowtimeSeats(ctx context.Context, showtimeID string) ([]domain.ShowtimeSeat, error) {
	builder := r.queryBuilder.Select(
		"seat_id", "showtime_id", "status", "price", "coalesce(booking_id, '') as booking_id",
	).From("showtime_seats").Where(squirrel.Eq{"showtime_id": showtimeID})
	query, args, err := builder.ToSql()
	if err != nil {
		return nil, fmt.Errorf("build get showtime seats query: %w", err)
	}
	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query showtime seats: %w", err)
	}
	defer rows.Close()
	seats := make([]domain.ShowtimeSeat, 0)
	for rows.Next() {
		var ss domain.ShowtimeSeat
		if err := rows.Scan(&ss.SeatID, &ss.ShowtimeID, &ss.Status, &ss.Price, &ss.BookingID); err != nil {
			return nil, fmt.Errorf("scan showtime seat: %w", err)
		}
		seats = append(seats, ss)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}
	return seats, nil
}
