package com.spring.userservice.Security.Service;

import com.spring.userservice.Models.User;
import io.jsonwebtoken.Jwts;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import static io.jsonwebtoken.security.Keys.hmacShaKeyFor;

@Service
public class JwtService {
    // This service is responsible for validating JWT tokens.

    private final Long EXPIRATION_TIME = 3600000L; // 1 hour in milliseconds

    private SecretKey secretKey;

    @Value("${jwt.secret}")
    private String secretKeyString;

    @PostConstruct
    public void init() {
        byte[] keyBytes = secretKeyString.getBytes(StandardCharsets.UTF_8);
        secretKey = hmacShaKeyFor(keyBytes);
    }

    public String getUsernameFromToken(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getBody()
                .getSubject();
    }

    public boolean isTokenValid(String token, User user) {
        String username = getUsernameFromToken(token);
        return username.equals(user.getEmail()) && !isTokenExpired(token);
    }

    public boolean isTokenExpired(String token) {
        Date expirationDate = Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getBody()
                .getExpiration();
        return expirationDate.before(new Date());
    }
}