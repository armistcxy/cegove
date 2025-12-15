package repository

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"

	sq "github.com/Masterminds/squirrel"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type BookingRepository interface {
	InsertBooking(ctx context.Context, booking *domain.Booking) error
	ListBookings(ctx context.Context) ([]domain.Booking, error)
	GetBookingInformation(ctx context.Context, bookingID string) (*domain.Booking, error)

	ProcessPaymentWebhook(ctx context.Context, req domain.PaymentWebhookRequest) error
	ScanTicket(ctx context.Context, code string) (*domain.Ticket, error)
}

type bookingRepository struct {
	pool   *pgxpool.Pool
	logger *logging.Logger
}

func NewBookingRepository(pool *pgxpool.Pool, logger *logging.Logger) BookingRepository {
	return &bookingRepository{
		pool:   pool,
		logger: logger,
	}
}

func (r *bookingRepository) InsertBooking(ctx context.Context, booking *domain.Booking) error {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}
	defer func() {
		if err != nil {
			tx.Rollback(ctx)
		}
	}()

	// Set ID and timestamps
	if booking.ID == "" {
		booking.ID = uuid.New().String()
	}
	now := time.Now().UTC()
	booking.CreatedAt = now
	// Set expiration 15 minutes after creation
	booking.ExpiresAt = now.Add(15 * time.Minute)

	// Reserve requested seats: lock them and assign booking ID
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	seatIDInts := make([]string, len(booking.SeatIDs))
	for i, seatID := range booking.SeatIDs {
		seatIDInts[i] = seatID
	}

	sQuery, sArgs, err := builder.Update("showtime_seats").
		Set("status", domain.SeatStatusLocked).
		Set("booking_id", booking.ID).
		Where(sq.Eq{"showtime_id": booking.ShowtimeID}).
		Where(sq.Eq{"seat_id": seatIDInts}).
		ToSql()
	if err != nil {
		return err
	}
	r.logger.Debug("update showtime seats", "query", sQuery, "args", sArgs)

	if _, err = tx.Exec(ctx, sQuery, sArgs...); err != nil {
		log.Printf("Failed to lock seats: %v", err)
		return err
	}

	bQuery, bArgs, err := builder.Insert("bookings").Columns(
		"id", "user_id", "showtime_id", "total_price", "status", "created_at", "expires_at",
	).Values(
		booking.ID, booking.UserID, booking.ShowtimeID, booking.TotalPrice, booking.Status, booking.CreatedAt, booking.ExpiresAt,
	).ToSql()

	if err != nil {
		return err
	}

	if _, err = tx.Exec(ctx, bQuery, bArgs...); err != nil {
		log.Printf("Failed to insert booking: %v", err)
		return err
	}

	var movieTitle string
	mQuery, mArgs, err := builder.Select("series_title").From("movies").Join("showtimes ON movies.id::text = showtimes.movie_id").
		Where(sq.Eq{"showtimes.id": booking.ShowtimeID}).ToSql()
	if err != nil {
		return err
	}

	row := tx.QueryRow(ctx, mQuery, mArgs...)
	err = row.Scan(&movieTitle)
	if err != nil {
		log.Printf("Failed to get movie title: %v", err)
		return err
	}

	var cinemaName string
	cQuery, cArgs, err := builder.Select("cinemas.name").From("cinemas").Join("auditoriums ON cinemas.id::text = auditoriums.cinema_id::text").
		Join("showtimes ON auditoriums.id::text = showtimes.auditorium_id").
		Where(sq.Eq{"showtimes.id": booking.ShowtimeID}).ToSql()
	if err != nil {
		return err
	}
	row = tx.QueryRow(ctx, cQuery, cArgs...)
	err = row.Scan(&cinemaName)
	if err != nil {
		log.Printf("Failed to get cinema name: %v", err)
		return err
	}

	var auditoriumName string
	aQuery, aArgs, err := builder.Select("auditoriums.name").From("auditoriums").Join("showtimes ON auditoriums.id::text = showtimes.auditorium_id").
		Where(sq.Eq{"showtimes.id": booking.ShowtimeID}).ToSql()
	if err != nil {
		log.Printf("Failed to build auditorium query: %v", err)
		return err
	}
	row = tx.QueryRow(ctx, aQuery, aArgs...)
	err = row.Scan(&auditoriumName)
	if err != nil {
		return err
	}

	showtimeQuery, showtimeArgs, err := builder.Select("start_time").From("showtimes").Where(sq.Eq{"id": booking.ShowtimeID}).ToSql()
	if err != nil {
		return err
	}

	row = tx.QueryRow(ctx, showtimeQuery, showtimeArgs...)
	var showtime time.Time
	err = row.Scan(&showtime)
	if err != nil {
		return err
	}

	tickets := make([]domain.Ticket, 0)
	for _, seatID := range booking.SeatIDs {
		sQuery, sArgs, err := builder.Select("seat_number", "price").From("showtime_seats").
			Join("seats ON showtime_seats.seat_id::text = seats.id::text").
			Where(sq.Eq{"seat_id::text": seatID}).
			Where(sq.Eq{"showtime_id": booking.ShowtimeID}).
			ToSql()
		if err != nil {
			return err
		}
		row := tx.QueryRow(ctx, sQuery, sArgs...)
		var seatNumber string
		var price float64
		err = row.Scan(&seatNumber, &price)
		if err != nil {
			log.Printf("Failed to get seat number and price: %v", err)
			return err
		}
		t := domain.Ticket{
			ID:             uuid.New().String(),
			BookingID:      booking.ID,
			ShowtimeID:     booking.ShowtimeID,
			MovieTitle:     movieTitle,
			CinemaName:     cinemaName,
			AuditoriumName: auditoriumName,
			Showtime:       showtime,
			SeatNumber:     seatNumber,
			QRCode:         uuid.New().String(),
			Price:          price,
		}
		booking.TotalPrice += price
		tickets = append(tickets, t)
	}

	ticketQuery := builder.Insert("tickets").Columns(
		"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "auditorium_name",
		"showtime", "seat_number", "qr_code", "price",
	)

	for _, t := range tickets {
		ticketQuery = ticketQuery.Values(
			t.ID, t.BookingID, t.ShowtimeID, t.MovieTitle, t.CinemaName, t.AuditoriumName,
			t.Showtime, t.SeatNumber, t.QRCode, t.Price,
		)
	}
	query, args, err := ticketQuery.ToSql()
	if err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, query, args...); err != nil {
		log.Printf("Failed to insert tickets: %v", err)
		return err
	}

	bQuery, bArgs, err = builder.Update("bookings").
		Set("total_price", booking.TotalPrice).
		Where(sq.Eq{"id": booking.ID}).
		ToSql()
	if err != nil {
		return err
	}

	if _, err = tx.Exec(ctx, bQuery, bArgs...); err != nil {
		log.Printf("Failed to update booking total price: %v", err)
		return err
	}

	if err = tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit transaction: %w", err)
	}

	booking.Tickets = tickets

	return nil
}

func (r *bookingRepository) ListBookings(ctx context.Context) ([]domain.Booking, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)
	query, args, err := builder.Select(
		"id", "user_id", "showtime_id", "total_price", "status", "created_at", "expires_at",
	).From("bookings").ToSql()
	if err != nil {
		return nil, fmt.Errorf("build list bookings query: %w", err)
	}

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query bookings: %w", err)
	}
	defer rows.Close()

	bookings := make([]domain.Booking, 0)
	for rows.Next() {
		var b domain.Booking
		if err := rows.Scan(
			&b.ID, &b.UserID, &b.ShowtimeID, &b.TotalPrice, &b.Status, &b.CreatedAt, &b.ExpiresAt,
		); err != nil {
			return nil, fmt.Errorf("scan booking: %w", err)
		}
		bookings = append(bookings, b)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}
	return bookings, nil
}

func (r *bookingRepository) GetBookingInformation(ctx context.Context, bookingID string) (*domain.Booking, error) {
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)
	query, args, err := builder.Select(
		"id", "user_id", "showtime_id", "total_price", "status", "created_at", "expires_at",
	).From("bookings").Where(sq.Eq{"id": bookingID}).ToSql()
	if err != nil {
		return nil, fmt.Errorf("build get booking query: %w", err)
	}

	row := r.pool.QueryRow(ctx, query, args...)
	var b domain.Booking
	if err := row.Scan(
		&b.ID, &b.UserID, &b.ShowtimeID, &b.TotalPrice, &b.Status, &b.CreatedAt, &b.ExpiresAt,
	); err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("scan booking: %w", err)
	}

	tQuery, tArgs, err := builder.Select(
		"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "auditorium_name",
		"showtime", "seat_number", "qr_code", "price", "status", "created_at",
	).From("tickets").Where(sq.Eq{"booking_id": bookingID}).OrderBy("created_at").ToSql()
	if err != nil {
		return &b, fmt.Errorf("build tickets query: %w", err)
	}

	rows, err := r.pool.Query(ctx, tQuery, tArgs...)
	if err != nil {
		return &b, fmt.Errorf("query tickets: %w", err)
	}
	defer rows.Close()

	var tickets []domain.Ticket
	for rows.Next() {
		var t domain.Ticket
		if err := rows.Scan(
			&t.ID, &t.BookingID, &t.ShowtimeID, &t.MovieTitle, &t.CinemaName, &t.AuditoriumName,
			&t.Showtime, &t.SeatNumber, &t.QRCode, &t.Price, &t.Status, &t.CreatedAt,
		); err != nil {
			return &b, fmt.Errorf("scan ticket: %w", err)
		}
		tickets = append(tickets, t)
	}
	if err := rows.Err(); err != nil {
		return &b, fmt.Errorf("rows error: %w", err)
	}

	b.Tickets = tickets
	return &b, nil
}

func (r *bookingRepository) ProcessPaymentWebhook(ctx context.Context, req domain.PaymentWebhookRequest) error {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}
	defer func() {
		if err != nil {
			tx.Rollback(ctx)
		}
	}()

	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	// Check if booking exists and is not confirmed
	query, args, err := builder.Select("status").
		From("bookings").
		Where(sq.Eq{"id": req.BookingID}).ToSql()
	if err != nil {
		return fmt.Errorf("build select booking status query: %w", err)
	}

	row := tx.QueryRow(ctx, query, args...)
	var currentStatus domain.BookingStatus
	err = row.Scan(&currentStatus)
	if err != nil {
		if err == pgx.ErrNoRows {
			return fmt.Errorf("booking not found: %s", req.BookingID)
		}
		return fmt.Errorf("query booking status: %w", err)
	}
	if currentStatus == domain.BookingStatusConfirmed || currentStatus == domain.BookingStatusFailed {
		return fmt.Errorf("booking already processed")
	}

	// if payment status is success, change ticket status to active and booking status to confirmed
	if req.PaymentStatus == "SUCCESS" {
		tQuery, tArgs, err := builder.Update("tickets").
			Set("status", domain.TicketStatusActive).
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()
		if err != nil {
			return fmt.Errorf("build update ticket status query: %w", err)
		}
		if _, err := tx.Exec(ctx, tQuery, tArgs...); err != nil {
			return fmt.Errorf("update ticket status: %w", err)
		}

		bQuery, bArgs, err := builder.Update("bookings").
			Set("status", domain.BookingStatusConfirmed).
			Where(sq.Eq{"id": req.BookingID}).
			ToSql()
		if err != nil {
			return fmt.Errorf("build update booking status query: %w", err)
		}
		if _, err := tx.Exec(ctx, bQuery, bArgs...); err != nil {
			return fmt.Errorf("update booking status: %w", err)
		}

		log.Printf("Updating showtime seats status for booking %s", req.BookingID)

		ssQuery, ssArgs, err := builder.Update("showtime_seats").
			Set("status", domain.SeatStatusSold).
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()

		if err != nil {
			log.Printf("Failed to build update showtime seats status query: %v", err)
			return fmt.Errorf("build update showtime seats status query: %w", err)
		}
		if _, err := tx.Exec(ctx, ssQuery, ssArgs...); err != nil {
			log.Printf("Failed to update showtime seats status: %v", err)
			return fmt.Errorf("update showtime seats status: %w", err)
		}
	}

	// if payment status is failed, change ticket status to cancelled and booking status to failed
	if req.PaymentStatus == "FAILED" {
		tQuery, tArgs, err := builder.Update("tickets").
			Set("status", domain.TicketStatusCancelled).
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()
		if err != nil {
			return fmt.Errorf("build update ticket status query: %w", err)
		}
		if _, err := tx.Exec(ctx, tQuery, tArgs...); err != nil {
			return fmt.Errorf("update ticket status: %w", err)
		}

		bQuery, bArgs, err := builder.Update("bookings").
			Set("status", domain.BookingStatusFailed).
			Where(sq.Eq{"id": req.BookingID}).
			ToSql()
		if err != nil {
			return fmt.Errorf("build update booking status query: %w", err)
		}
		if _, err := tx.Exec(ctx, bQuery, bArgs...); err != nil {
			return fmt.Errorf("update booking status: %w", err)
		}
	}

	if err = tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit transaction: %w", err)
	}

	return nil
}

func (r *bookingRepository) ScanTicket(ctx context.Context, code string) (*domain.Ticket, error) {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer func() {
		if err != nil {
			tx.Rollback(ctx)
		}
	}()

	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)
	query, args, err := builder.Select(
		"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "auditorium_name",
		"showtime", "seat_number", "qr_code", "price", "status", "created_at",
	).From("tickets").Where(sq.Eq{"qr_code": code}).Suffix("FOR UPDATE").ToSql()
	if err != nil {
		return nil, fmt.Errorf("build select ticket query: %w", err)
	}

	var t domain.Ticket
	row := tx.QueryRow(ctx, query, args...)
	if err := row.Scan(
		&t.ID, &t.BookingID, &t.ShowtimeID, &t.MovieTitle, &t.CinemaName, &t.AuditoriumName,
		&t.Showtime, &t.SeatNumber, &t.QRCode, &t.Price, &t.Status, &t.CreatedAt,
	); err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("scan ticket: %w", err)
	}

	if t.Status != domain.TicketStatusActive {
		return nil, fmt.Errorf("ticket not valid or already used")
	}

	// Mark ticket as used
	uQuery, uArgs, err := builder.Update("tickets").
		Set("status", domain.TicketStatusUsed).
		Where(sq.Eq{"id": t.ID}).
		ToSql()
	if err != nil {
		return nil, fmt.Errorf("build update ticket status query: %w", err)
	}
	if _, err := tx.Exec(ctx, uQuery, uArgs...); err != nil {
		return nil, fmt.Errorf("update ticket status: %w", err)
	}

	if err = tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("commit scan ticket transaction: %w", err)
	}
	return &t, nil
}
