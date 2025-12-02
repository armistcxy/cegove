package com.spring.userservice.Reposistories;

import com.spring.userservice.Models.Booking;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookingReposistory extends JpaRepository<Booking, Long> {
    List<Booking> findByUserId(Long userId);
}
