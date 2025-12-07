package com.spring.authservice.Services;

import com.spring.authservice.DTOs.ChangeForgotPasswordRequest;
import com.spring.authservice.DTOs.LoginRequest;
import com.spring.authservice.DTOs.RegisterRequest;
import com.spring.authservice.DTOs.VerifyOtpRequest;
import com.spring.authservice.Enums.Provider;
import com.spring.authservice.Enums.UserRole;
import com.spring.authservice.Exceptions.InvalidCredentialsException;
import com.spring.authservice.Exceptions.NotAuthorizeException;
import com.spring.authservice.Exceptions.UserAlreadyExistedException;
import com.spring.authservice.Models.User;
import com.spring.authservice.Reposistories.UserReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class AuthService {
    @Autowired
    private UserReposistory reposistory;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private RedisService redisService;

    @Autowired
    private ImageUploadClient imageUploadClient;

    @Autowired
    private MailSenderClient mailSenderClient;

    private PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public String login(LoginRequest request) {
        Optional<User> user = reposistory.findByEmail(request.getUsername());
        if (!user.isPresent()) {
            user = reposistory.findByPhone(request.getUsername());
        }

        if (!user.isPresent()) {
            throw new UsernameNotFoundException("User not found with email/phone: " + request.getUsername());
        }

        if (!user.get().getProvider().equals(Provider.SELF)) {
            throw new NotAuthorizeException("Please login with " + user.get().getProvider() + " account");
        }

        if (!passwordEncoder.matches(request.getPassword(), user.get().getPassword())) {
            throw new InvalidCredentialsException("Invalid password");
        }

        return jwtService.generateToken(user.get());
    }

    public void register(RegisterRequest request) {
        Optional<User> user = reposistory.findByEmail(request.getEmail());
        if (user.isPresent()) {
            throw new UserAlreadyExistedException("User with email " + request.getEmail() + " already existed");
        }

        user = reposistory.findByPhone(request.getPhone());
        if (user.isPresent()) {
            throw new UserAlreadyExistedException("User with phone number " + request.getPhone() + " already existed");
        }

        User newUser = User.builder()
                .fullName(request.getFullName())
                .email(request.getEmail())
                .phone(request.getPhone())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(UserRole.USER)
                .dob(request.getDob())
                .gender(request.getGender())
                .address(request.getAddress())
                .district(request.getDistrict())
                .city(request.getCity())
                .provider(Provider.SELF).build();

        if (request.getImg() != null && !request.getImg().isEmpty()) {
            newUser.setImg(imageUploadClient.uploadImage(request.getImg()));
        }

        reposistory.save(newUser);
    }

    public void logout(String token) {
        if (token != null) {
            long expiration = jwtService.getExpirationTime(token);
            redisService.blacklistToken(token, expiration);
        }
    }

    public void sendMailResetPassword(String email) {
        Optional<User> user = reposistory.findByEmail(email);
        if (!user.isPresent()) {
            throw new UsernameNotFoundException("User not found with email: " + email);
        }

        String otp = ThreadLocalRandom.current().nextInt(100000, 1000000) + "";
        redisService.storeOtp(email, otp);

        // Send OTP email
        mailSenderClient.sendPasswordResetOTP(email, otp);
    }

    public boolean verifyOtp(VerifyOtpRequest request) {
        return redisService.verifyOtp(request.getEmail(), request.getOtp());
    }

    public void changeForgotPassword(ChangeForgotPasswordRequest request) {
        if (!redisService.verifyOtp(request.getEmail(), request.getOtp())) {
            throw new InvalidCredentialsException("Invalid OTP");
        }

        if (!request.getNewPassword().equals(request.getConfirmPassword())) {
            throw new InvalidCredentialsException("New password and confirm new password do not match");
        }

        redisService.removeOtp(request.getEmail());
        User user = reposistory.findByEmail(request.getEmail())
                .orElseThrow(() -> new UsernameNotFoundException("User not found with email: " + request.getEmail()));

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        reposistory.save(user);
    }
}
