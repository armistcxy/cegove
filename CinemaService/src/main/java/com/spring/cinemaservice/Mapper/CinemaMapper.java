package com.spring.cinemaservice.Mapper;

import com.spring.cinemaservice.DTOs.CinemaRequest;
import com.spring.cinemaservice.DTOs.CinemaResponse;
import com.spring.cinemaservice.Models.Cinema;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface CinemaMapper {
    @Mapping(target = "images", ignore = true)
    Cinema toEntity(CinemaRequest request);

    CinemaResponse toResponse(Cinema entity);
}
