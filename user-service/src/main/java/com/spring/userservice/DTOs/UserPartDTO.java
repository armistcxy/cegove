package com.spring.userservice.DTOs;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserPartDTO {
    private Long id;
    private String fullName;
    private String email;
    private String img;
}