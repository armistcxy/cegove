package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Cinema;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface CinemaReposistory extends JpaRepository<Cinema, Long> {

    @Override
    @EntityGraph(attributePaths = {"images"})
    List<Cinema> findAll();

    @Override
    @EntityGraph(attributePaths = {"images"})
    Optional<Cinema> findById(Long aLong);

    @EntityGraph(attributePaths = {"images"})
    List<Cinema> findByCityIgnoreCase(String city);
}
