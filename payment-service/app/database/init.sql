-- -------------------------------------------------------------
-- Movie Booking System (PostgreSQL Schema)
-- -------------------------------------------------------------

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  full_name TEXT,
  phone TEXT,
  role TEXT, -- user, admin, staff
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE movies (
  id BIGINT PRIMARY KEY, -- match TMDB movie_id for easier import
  title TEXT,
  original_title TEXT,
  overview TEXT,
  release_date DATE,
  runtime INT,
  language TEXT,
  budget NUMERIC(15,2),
  revenue NUMERIC(15,2),
  poster_path TEXT,
  backdrop_path TEXT,
  vote_average FLOAT,
  vote_count INT,
  popularity FLOAT,
  genres TEXT, -- can store JSON or comma-separated
  production_companies TEXT,
  production_countries TEXT,
  keywords TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ratings (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  movie_id BIGINT REFERENCES movies(id),
  rating FLOAT,
  rated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (user_id, movie_id)
);

CREATE TABLE cinemas (
  id BIGSERIAL PRIMARY KEY,
  name TEXT,
  address TEXT,
  city TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE auditoriums (
  id BIGSERIAL PRIMARY KEY,
  cinema_id BIGINT REFERENCES cinemas(id),
  name TEXT,
  total_seats INT
);

CREATE TABLE seats (
  id BIGSERIAL PRIMARY KEY,
  auditorium_id BIGINT REFERENCES auditoriums(id),
  seat_number TEXT,
  seat_type TEXT, -- Normal, VIP, Couple
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE screenings (
  id BIGSERIAL PRIMARY KEY,
  movie_id BIGINT REFERENCES movies(id),
  auditorium_id BIGINT REFERENCES auditoriums(id),
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  base_price NUMERIC(10,2),
  status TEXT -- scheduled, cancelled, finished
);

CREATE TABLE bookings (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  screening_id BIGINT REFERENCES screenings(id),
  total_amount NUMERIC(10,2),
  status TEXT, -- pending, paid, cancelled
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE booking_seats (
  id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT REFERENCES bookings(id),
  seat_id BIGINT REFERENCES seats(id),
  price NUMERIC(10,2)
);

CREATE TABLE payments (
  id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT REFERENCES bookings(id),
  provider TEXT, -- VNPay, MoMo, Stripe
  amount NUMERIC(10,2),
  status TEXT, -- success, failed, pending
  transaction_time TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notifications (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  type TEXT, -- booking_confirm, reminder, promo
  title TEXT,
  message TEXT,
  is_sent BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recommendations (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  movie_id BIGINT REFERENCES movies(id),
  score FLOAT,
  reason TEXT, -- e.g. "similar genre", "popular", "your rating history"
  created_at TIMESTAMPTZ DEFAULT now()
);

