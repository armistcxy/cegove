package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserReposistory extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}
