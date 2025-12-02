package com.spring.cinemaservice.DTOs;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CinemaRequest {
    private String name;
    private String address;
    private String district;
    private String city;
    private String phone;
    private List<MultipartFile> images;

    private List<AuditoriumDTO> auditoriumList;
}
