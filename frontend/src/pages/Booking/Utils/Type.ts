export interface Showtime {
    id: string;
    movie_id: number;
    cinema_id: number;
    auditorium_id: number;
    start_time: string;
    end_time: string;
    base_price: number;
}

export interface Seat {
    seat_id: number;
    showtime_id: string;
    status: 0 | 1;
    price: number;
    seat_number: string;
    seat_type: "STANDARD" | "VIP" | "COUPLE";
}