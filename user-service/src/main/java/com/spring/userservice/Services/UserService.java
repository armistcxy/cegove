package com.spring.userservice.Services;

import com.spring.userservice.DTOs.BookingDTO;
import com.spring.userservice.DTOs.ChangePasswordForm;
import com.spring.userservice.DTOs.TicketDTO;
import com.spring.userservice.DTOs.UserDTO;
import com.spring.userservice.DTOs.UserPartDTO;
import com.spring.userservice.Enums.Provider;
import com.spring.userservice.Enums.UserRole;
import com.spring.userservice.Exceptions.ActionNotAllowedException;
import com.spring.userservice.Exceptions.InvalidCredentialsException;
import com.spring.userservice.Exceptions.UserAlreadyExistedException;
import com.spring.userservice.Models.User;
import com.spring.userservice.Reposistories.BookingReposistory;
import com.spring.userservice.Reposistories.UserReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class UserService {
    @Autowired
    private UserReposistory repository;

    @Autowired
    private BookingReposistory bookingRepository;

    @Autowired
    private ImageUploadClient imageUploadClient;

    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public User getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        return repository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with email: " + email));
    }

    public UserDTO profile() {
        User user = getCurrentUser();
        return user.convertToDTO();
    }

    public UserPartDTO getUserProfile(Long userId) {
        User user = repository.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with id: " + userId));
        return user.convertToPartDTO();
    }

    public void changePassword(ChangePasswordForm changePasswordForm) {
        User currentUser = getCurrentUser();
        if (currentUser.getProvider().equals(Provider.GOOGLE)) {
            throw new ActionNotAllowedException("Cannot update profile for Google authenticated users.");
        }

        if (!passwordEncoder.matches(changePasswordForm.getOldPassword(), currentUser.getPassword())) {
            throw new InvalidCredentialsException("Old password does not match");
        }

        currentUser.setPassword(passwordEncoder.encode(changePasswordForm.getNewPassword()));
        repository.save(currentUser);
    }

    public void updateProfile(UserDTO updatedUser) {
        User currentUser = getCurrentUser();

        if (updatedUser.getEmail() != null
                && !updatedUser.getEmail().equals(currentUser.getEmail())
                && currentUser.getProvider().equals(Provider.SELF)) {
            Optional<User> existingUser = repository.findByEmail(updatedUser.getEmail());
            if (existingUser.isPresent()) {
                throw new UserAlreadyExistedException("User with this email already exists.");
            }
            currentUser.setEmail(updatedUser.getEmail());
        }

        if (updatedUser.getPhone() != null && !updatedUser.getPhone().equals(currentUser.getPhone())) {
            Optional<User> existingUser = repository.findByPhone(updatedUser.getPhone());
            if (existingUser.isPresent()) {
                throw new UserAlreadyExistedException("User with this phone number already exists.");
            }
            currentUser.setPhone(updatedUser.getPhone());
        }

        if (updatedUser.getFullName() != null) {
            currentUser.setFullName(updatedUser.getFullName());
        }

        if (updatedUser.getAddress() != null) {
            currentUser.setAddress(updatedUser.getAddress());
        }
        if (updatedUser.getDistrict() != null) {
            currentUser.setDistrict(updatedUser.getDistrict());
        }
        if (updatedUser.getCity() != null) {
            currentUser.setCity(updatedUser.getCity());
        }

        if (updatedUser.getDob() != null) {
            currentUser.setDob(updatedUser.getDob());
        }

        if (updatedUser.getGender() != null) {
            currentUser.setGender(updatedUser.getGender());
        }

        if (updatedUser.getImgFile() != null) {
            String imageUrl = imageUploadClient.uploadImage(updatedUser.getImgFile());
            currentUser.setImg(imageUrl);
        }

        repository.save(currentUser);
    }

    public List<BookingDTO> bookingHistory() {
        User currentUser = getCurrentUser();
        List<BookingDTO> bookings =
                bookingRepository.findBookingDTOByUserId(currentUser.getId());

        if (bookings.isEmpty()) return bookings;

        List<String> bookingIds = bookings.stream()
                .map(BookingDTO::getId)
                .toList();

        Map<String, List<TicketDTO>> ticketMap =
                bookingRepository.findTicketsByBookingIds(bookingIds)
                        .stream()
                        .collect(Collectors.groupingBy(TicketDTO::getBookingId));

        bookings.forEach(b ->
                b.setTickets(ticketMap.getOrDefault(b.getId(), List.of()))
        );

        return bookings;
    }

    public List<UserDTO> getAllUsers() {
        List<User> users = repository.findAll();
        return users.stream()
                .map(User::convertToDTO)
                .toList();
    }

    public void deleteUser(Long userId) {
        User user = repository.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with id: " + userId));
        repository.delete(user);
    }

    public void changeRoleUser(Long userId, String role) {
        User user = repository.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with id: " + userId));
        user.setRole(UserRole.valueOf(role));
        repository.save(user);
    }
}
