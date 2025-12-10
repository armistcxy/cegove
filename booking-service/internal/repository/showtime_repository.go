package repository

import (
	"context"
	"fmt"

	"github.com/armistcxy/cegove/booking-service/internal/domain"

	"github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5/pgxpool"
)

type ShowtimeRepository interface {
	ListShowtimes(ctx context.Context, movieID, cinemaID string) ([]domain.Showtime, error)
	GetShowtimeSeats(ctx context.Context, showtimeID string) ([]domain.ShowtimeSeat, error)

	InsertShowtimes(ctx context.Context, showtimes []domain.Showtime) error
	InsertShowtimeSeats(ctx context.Context, showtimeID string, seats []domain.ShowtimeSeat) error
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

func (r *showtimeRepository) ListShowtimes(ctx context.Context, movieID, cinemaID string) ([]domain.Showtime, error) {
	builder := r.queryBuilder.Select(
		"id", "movie_id", "cinema_id", "auditorium_id", "start_time", "end_time", "base_price",
	).From("showtimes")
	if movieID != "" {
		builder = builder.Where(squirrel.Eq{"movie_id": movieID})
	}
	if cinemaID != "" {
		builder = builder.Where(squirrel.Eq{"cinema_id": cinemaID})
	}
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
			&st.ID, &st.MovieID, &st.CinemaID, &st.AuditoriumID, &st.StartTime, &st.EndTime, &st.BasePrice,
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
		"seat_id", "showtime_id", "status", "price", "coalesce(booking_id, '') as booking_id", "seat_number", "seat_type",
	).From("showtime_seats").Join("seats ON seats.id::text = showtime_seats.seat_id")
	builder = builder.Where(squirrel.Eq{"showtime_id": showtimeID})
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
		if err := rows.Scan(&ss.SeatID, &ss.ShowtimeID, &ss.Status, &ss.Price, &ss.BookingID, &ss.SeatNumber, &ss.SeatType); err != nil {
			return nil, fmt.Errorf("scan showtime seat: %w", err)
		}
		seats = append(seats, ss)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}
	return seats, nil
}

func (r *showtimeRepository) InsertShowtimes(ctx context.Context, showtimes []domain.Showtime) error {
	builder := r.queryBuilder.Insert("showtimes").Columns(
		"id", "movie_id", "cinema_id", "auditorium_id", "start_time", "end_time", "base_price",
	)
	for _, st := range showtimes {
		builder = builder.Values(st.ID, st.MovieID, st.CinemaID, st.AuditoriumID, st.StartTime, st.EndTime, st.BasePrice)
	}
	query, args, err := builder.ToSql()
	if err != nil {
		return fmt.Errorf("build insert showtimes query: %w", err)
	}
	if _, err := r.pool.Exec(ctx, query, args...); err != nil {
		return fmt.Errorf("insert showtimes: %w", err)
	}
	return nil
}

func (r *showtimeRepository) InsertShowtimeSeats(ctx context.Context, showtimeID string, seats []domain.ShowtimeSeat) error {
	builder := r.queryBuilder.Insert("showtime_seats").Columns(
		"seat_id", "showtime_id", "status", "price",
	)
	for _, ss := range seats {
		builder = builder.Values(ss.SeatID, showtimeID, ss.Status, ss.Price)
	}
	query, args, err := builder.ToSql()
	if err != nil {
		return fmt.Errorf("build insert showtime seats query: %w", err)
	}
	if _, err := r.pool.Exec(ctx, query, args...); err != nil {
		return fmt.Errorf("insert showtime seats: %w", err)
	}
	return nil
}
