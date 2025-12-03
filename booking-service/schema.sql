CREATE TABLE seats (
    id VARCHAR(255) PRIMARY KEY,
    screen_id VARCHAR(255) NOT NULL,
    row_name VARCHAR(10) NOT NULL,
    seat_number INT NOT NULL,
    seat_type SMALLINT NOT NULL
);

CREATE INDEX idx_seats_on_screen_id ON seats(screen_id);

CREATE TABLE showtimes (
    id VARCHAR(255) PRIMARY KEY,
    movie_id VARCHAR(255) NOT NULL,
    cinema_id VARCHAR(255),
    screen_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE showtime_seats (
    seat_id VARCHAR(255) NOT NULL,
    showtime_id VARCHAR(255) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    booking_id VARCHAR(255),

    PRIMARY KEY (seat_id, showtime_id)
);

CREATE INDEX idx_showtime_seats_on_showtime_id ON showtime_seats(showtime_id);

CREATE TABLE bookings (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    showtime_id VARCHAR(255) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_bookings_on_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_on_showtime_id ON bookings(showtime_id);

CREATE TABLE tickets (
    id VARCHAR(255) PRIMARY KEY,
    booking_id VARCHAR(255) NOT NULL REFERENCES bookings(id),
    showtime_id VARCHAR(255) NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    cinema_name VARCHAR(255) NOT NULL,
    screen_name VARCHAR(255) NOT NULL,
    showtime TIMESTAMPTZ NOT NULL,
    seat_row VARCHAR(10) NOT NULL,
    seat_number INT NOT NULL,

    qr_code TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_on_booking_id ON tickets(booking_id);