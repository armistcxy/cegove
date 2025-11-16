package com.spring.userservice.Services;

import com.spring.userservice.Models.User;
import com.spring.userservice.Reposistories.UserReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    // Implement the methods required by UserDetailsService
    // For example, loadUserByUsername(String username) to fetch user details from the database

    @Autowired
    private UserReposistory userRepository;

    @Override
    public User loadUserByUsername(String username) {
        User user = userRepository.findByEmail(username)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with email: " + username));
        return user;
    }
}
