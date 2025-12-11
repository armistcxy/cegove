package com.spring.userservice.DTOs;

import lombok.Data;

@Data
public class ChangePasswordForm {
    private String oldPassword;
    private String newPassword;
}
