package com.spring.cinemaservice.Enums;

import com.spring.cinemaservice.Models.Seat;

import java.util.ArrayList;
import java.util.List;

public enum AuditoriumPattern {
    ONE {
        @Override
        public List<Seat> generateSeats() {
            List<Seat> seats = new ArrayList<>();

            seats.addAll(createSeats('A', 'C', 19, SeatType.STANDARD));
            seats.addAll(createSeats('D', 'H', 19, SeatType.VIP));
            seats.addAll(createSeats('K', 'K', 7, SeatType.COUPLE));

            return seats;
        }
    },
    TWO {
        @Override
        public List<Seat> generateSeats() {
            List<Seat> seats = new ArrayList<>();

            seats.addAll(createSeats('A', 'C', 26, SeatType.STANDARD));
            seats.addAll(createSeats('D', 'J', 26, SeatType.VIP));
            seats.addAll(createSeats('L', 'L', 13, SeatType.COUPLE));

            return seats;
        }
    },
    THREE {
        @Override
        public List<Seat> generateSeats() {
            List<Seat> seats = new ArrayList<>();

            seats.addAll(createSeats('A', 'C', 10, SeatType.STANDARD));
            seats.addAll(createSeats('D', 'J', 10, SeatType.VIP));
            seats.addAll(createSeats('K', 'K', 5, SeatType.COUPLE));

            return seats;
        }
    };

    public abstract List<Seat> generateSeats();

    protected List<Seat> createSeats(char startRow, char endRow, int count, SeatType type) {
        List<Seat> list = new ArrayList<>();
        for (char row = startRow; row <= endRow; row++) {
            for (int i = 1; i <= count; i++) {
                list.add(Seat.builder()
                        .seatNumber(row + String.valueOf(i))
                        .seatType(type)
                        .build());
            }
        }
        return list;
    }
}
