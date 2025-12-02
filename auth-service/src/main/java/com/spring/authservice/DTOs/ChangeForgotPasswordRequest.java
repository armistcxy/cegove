package com.spring.authservice.DTOs;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChangeForgotPasswordRequest {
    private String email;
    private String otp;
    private String newPassword;
    private String confirmPassword;
}
