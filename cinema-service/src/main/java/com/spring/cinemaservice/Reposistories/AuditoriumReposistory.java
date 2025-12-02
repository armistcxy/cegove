package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Auditorium;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AuditoriumReposistory extends JpaRepository<Auditorium, Long> {

}
