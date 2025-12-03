package repository

import (
	"context"
	"encoding/base64"
	"fmt"
	"strconv"
	"time"

	"github.com/skip2/go-qrcode"

	"github.com/armistcxy/cegove/booking-service/internal/domain"

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
	pool *pgxpool.Pool
}

func NewBookingRepository(pool *pgxpool.Pool) BookingRepository {
	return &bookingRepository{
		pool: pool,
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
	builder2 := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)
	updateQuery, updateArgs, err := builder2.Update("showtime_seats").
		Set("status", domain.SeatStatusLocked).
		Set("booking_id", booking.ID).
		Where(sq.And{
			sq.Eq{"showtime_id": booking.ShowtimeID},
			sq.Eq{"seat_id": booking.SeatIDs},
			sq.Eq{"status": domain.SeatStatusAvailable},
		}).
		ToSql()
	if err != nil {
		return fmt.Errorf("build reserve seats query: %w", err)
	}
	res, err := tx.Exec(ctx, updateQuery, updateArgs...)
	if err != nil {
		return fmt.Errorf("reserve seats: %w", err)
	}
	if res.RowsAffected() != int64(len(booking.SeatIDs)) {
		return fmt.Errorf("some seats are no longer available")
	}

	// Calculate total price from reserved seats
	priceQuery, priceArgs, err := builder2.Select("price").
		From("showtime_seats").
		Where(sq.Eq{"showtime_id": booking.ShowtimeID, "booking_id": booking.ID}).
		ToSql()
	if err != nil {
		return fmt.Errorf("build price query: %w", err)
	}
	rows, err := tx.Query(ctx, priceQuery, priceArgs...)
	if err != nil {
		return fmt.Errorf("query reserved seats prices: %w", err)
	}
	defer rows.Close()
	var total float64
	for rows.Next() {
		var p float64
		if err := rows.Scan(&p); err != nil {
			return fmt.Errorf("scan seat price: %w", err)
		}
		total += p
	}
	booking.TotalPrice = total

	// Prepare tickets for each reserved seat
	booking.Tickets = make([]domain.Ticket, 0, len(booking.SeatIDs))
	for _, seatID := range booking.SeatIDs {
		// derive row and number from seatID (e.g., "A10")
		row := string(seatID[0])
		num, _ := strconv.Atoi(seatID[1:])
		t := domain.Ticket{
			ID:         uuid.New().String(),
			BookingID:  booking.ID,
			ShowtimeID: booking.ShowtimeID,
			SeatRow:    row,
			SeatNumber: num,
			Price:      0, // will be set by insert based on booking.TotalPrice split if needed
			Status:     domain.TicketStatusActive,
			CreatedAt:  now,
		}
		booking.Tickets = append(booking.Tickets, t)
	}

	// Insert booking record
	builder := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)
	query, args, err := builder.Insert("bookings").
		Columns("id", "user_id", "showtime_id", "total_price", "status", "created_at", "expires_at").
		Values(booking.ID, booking.UserID, booking.ShowtimeID, booking.TotalPrice, booking.Status, booking.CreatedAt, booking.ExpiresAt).
		ToSql()
	if err != nil {
		return fmt.Errorf("build insert booking query: %w", err)
	}
	if _, err = tx.Exec(ctx, query, args...); err != nil {
		return fmt.Errorf("insert booking: %w", err)
	}

	// Insert tickets
	for _, t := range booking.Tickets {
		if t.ID == "" {
			t.ID = uuid.New().String()
		}
		if t.CreatedAt.IsZero() {
			t.CreatedAt = now
		}
		tQuery, tArgs, err := builder.Insert("tickets").
			Columns(
				"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "screen_name",
				"showtime", "seat_row", "seat_number", "qr_code", "price", "status", "created_at",
			).
			Values(
				t.ID, booking.ID, t.ShowtimeID, t.MovieTitle, t.CinemaName, t.ScreenName,
				t.Showtime, t.SeatRow, t.SeatNumber, t.QRCode, t.Price, t.Status, t.CreatedAt,
			).
			ToSql()
		if err != nil {
			return fmt.Errorf("build insert ticket query: %w", err)
		}
		if _, err = tx.Exec(ctx, tQuery, tArgs...); err != nil {
			return fmt.Errorf("insert ticket %s: %w", t.ID, err)
		}
	}

	if err = tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit transaction: %w", err)
	}
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
		"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "screen_name",
		"showtime", "seat_row", "seat_number", "qr_code", "price", "status", "created_at",
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
			&t.ID, &t.BookingID, &t.ShowtimeID, &t.MovieTitle, &t.CinemaName, &t.ScreenName,
			&t.Showtime, &t.SeatRow, &t.SeatNumber, &t.QRCode, &t.Price, &t.Status, &t.CreatedAt,
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

	query, args, err := builder.Select("status").
		From("bookings").
		Where(sq.Eq{"id": req.BookingID}).
		Suffix("FOR UPDATE").
		ToSql()
	if err != nil {
		return fmt.Errorf("build select booking query: %w", err)
	}

	var currentStatus domain.BookingStatus
	err = tx.QueryRow(ctx, query, args...).Scan(&currentStatus)
	if err != nil {
		if err == pgx.ErrNoRows {
			return fmt.Errorf("booking not found: %s", req.BookingID)
		}
		return fmt.Errorf("query booking status: %w", err)
	}

	// Idempotency check
	// If booking is already Confirmed or Failed, we do nothing and return success
	if currentStatus == domain.BookingStatusConfirmed || currentStatus == domain.BookingStatusFailed {
		return nil
	}

	// Update booking status
	if req.PaymentStatus == "SUCCESS" {
		// Pending -> Confirmed
		uQuery, uArgs, err := builder.Update("bookings").
			Set("status", domain.BookingStatusConfirmed).
			Where(sq.Eq{"id": req.BookingID}).
			ToSql()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, uQuery, uArgs...); err != nil {
			return fmt.Errorf("update booking confirmed: %w", err)
		}

		// Locked -> Sold
		sQuery, sArgs, err := builder.Update("showtime_seats").
			Set("status", domain.SeatStatusSold).
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, sQuery, sArgs...); err != nil {
			return fmt.Errorf("update seats sold: %w", err)
		}

		// Generate and update QR codes for tickets
		rows, err := tx.Query(ctx, "SELECT id FROM tickets WHERE booking_id=$1", req.BookingID)
		if err != nil {
			return fmt.Errorf("query tickets for QR generation: %w", err)
		}
		defer rows.Close()
		for rows.Next() {
			var ticketID string
			if err := rows.Scan(&ticketID); err != nil {
				return fmt.Errorf("scan ticket id: %w", err)
			}
			png, err := qrcode.Encode(ticketID, qrcode.Medium, 256)
			if err != nil {
				return fmt.Errorf("generate QR code: %w", err)
			}
			qrB64 := base64.StdEncoding.EncodeToString(png)
			uQrQuery, uQrArgs, err := builder.Update("tickets").
				Set("qr_code", qrB64).
				Where(sq.Eq{"id": ticketID}).
				ToSql()
			if err != nil {
				return fmt.Errorf("build update qr query: %w", err)
			}
			if _, err := tx.Exec(ctx, uQrQuery, uQrArgs...); err != nil {
				return fmt.Errorf("update ticket qr code: %w", err)
			}
		}

	} else {
		// Pending -> Failed
		uQuery, uArgs, err := builder.Update("bookings").
			Set("status", domain.BookingStatusFailed).
			Where(sq.Eq{"id": req.BookingID}).
			ToSql()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, uQuery, uArgs...); err != nil {
			return fmt.Errorf("update booking failed: %w", err)
		}

		// Locked -> Available
		sQuery, sArgs, err := builder.Update("showtime_seats").
			Set("status", domain.SeatStatusAvailable).
			Set("booking_id", nil). // Clear the relationship
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, sQuery, sArgs...); err != nil {
			return fmt.Errorf("release seats: %w", err)
		}

		// cancel ticket
		tQuery, tArgs, err := builder.Update("tickets").
			Set("status", domain.TicketStatusCancelled).
			Where(sq.Eq{"booking_id": req.BookingID}).
			ToSql()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, tQuery, tArgs...); err != nil {
			return fmt.Errorf("cancel tickets: %w", err)
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
		"id", "booking_id", "showtime_id", "movie_title", "cinema_name", "screen_name",
		"showtime", "seat_row", "seat_number", "qr_code", "price", "status", "created_at",
	).From("tickets").Where(sq.Eq{"qr_code": code}).Suffix("FOR UPDATE").ToSql()
	if err != nil {
		return nil, fmt.Errorf("build select ticket query: %w", err)
	}

	var t domain.Ticket
	row := tx.QueryRow(ctx, query, args...)
	if err := row.Scan(
		&t.ID, &t.BookingID, &t.ShowtimeID, &t.MovieTitle, &t.CinemaName, &t.ScreenName,
		&t.Showtime, &t.SeatRow, &t.SeatNumber, &t.QRCode, &t.Price, &t.Status, &t.CreatedAt,
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
