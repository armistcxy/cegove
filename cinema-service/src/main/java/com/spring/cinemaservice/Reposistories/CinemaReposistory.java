package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Cinema;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CinemaReposistory extends JpaRepository<Cinema, Long> {
}
