CREATE TABLE showtimes (
    id TEXT PRIMARY KEY,
    movie_id TEXT NOT NULL,
    cinema_id TEXT,
    auditorium_id TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE showtime_seats (
    seat_id TEXT NOT NULL,
    showtime_id TEXT NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    booking_id TEXT,

    PRIMARY KEY (seat_id, showtime_id)
);

CREATE INDEX idx_showtime_seats_on_showtime_id ON showtime_seats(showtime_id);

CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    showtime_id TEXT NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_bookings_on_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_on_showtime_id ON bookings(showtime_id);

CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL REFERENCES bookings(id),
    showtime_id TEXT NOT NULL,
    movie_title TEXT NOT NULL,
    cinema_name TEXT NOT NULL,
    auditorium_name TEXT NOT NULL,
    showtime TIMESTAMPTZ NOT NULL,
    seat_number TEXT NOT NULL,

    price DECIMAL(10, 2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_on_booking_id ON tickets(booking_id);

-- Food items table
CREATE TABLE food_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    image_url TEXT,
    available BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_food_items_on_type ON food_items(type);
CREATE INDEX idx_food_items_on_category ON food_items(category);
CREATE INDEX idx_food_items_on_available ON food_items(available);

-- Booking food items association table
CREATE TABLE booking_food_items (
    id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL REFERENCES bookings(id),
    food_item_id TEXT NOT NULL REFERENCES food_items(id),
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_booking_food_items_on_booking_id ON booking_food_items(booking_id);
CREATE INDEX idx_booking_food_items_on_food_item_id ON booking_food_items(food_item_id);