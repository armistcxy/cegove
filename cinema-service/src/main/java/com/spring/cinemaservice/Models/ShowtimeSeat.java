package com.spring.cinemaservice.Models;

import jakarta.persistence.Embeddable;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Objects;

@Entity
@Table(name = "showtime_seats")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ShowtimeSeat {
    @EmbeddedId
    private ShowtimeSeatId id;

    private int status;
    private BigDecimal price;
    private String bookingId;

    @Embeddable
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ShowtimeSeatId implements Serializable {
        private String showtimeId;
        private Long seatId;

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof ShowtimeSeatId)) return false;
            ShowtimeSeatId that = (ShowtimeSeatId) o;
            return Objects.equals(showtimeId, that.showtimeId) &&
                    Objects.equals(seatId, that.seatId);
        }

        @Override
        public int hashCode() {
            return Objects.hash(showtimeId, seatId);
        }
    }
}
