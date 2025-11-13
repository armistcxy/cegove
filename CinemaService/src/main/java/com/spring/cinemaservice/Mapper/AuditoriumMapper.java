package com.spring.cinemaservice.Mapper;

import com.spring.cinemaservice.DTOs.AuditoriumDTO;
import com.spring.cinemaservice.Models.Auditorium;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface AuditoriumMapper {
    Auditorium toEntity(AuditoriumDTO request);

    AuditoriumDTO toResponse(Auditorium entity);
}
