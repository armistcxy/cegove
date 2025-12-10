package com.spring.cinemaservice.Models;

import com.spring.cinemaservice.DTOs.CinemaResponse;
import jakarta.persistence.CascadeType;
import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "cinemas")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Cinema {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    private String address;
    private String district;
    private String city;

    private String phone;

    @ElementCollection
    @CollectionTable(
            name = "cinema_images",
            joinColumns = @JoinColumn(name = "cinema_id")
    )
    @Column(name = "image_url")
    private List<String> images;

    @OneToMany(mappedBy = "cinema", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private List<Auditorium> auditoriums = new ArrayList<>();

    private final LocalDate createdAt = LocalDate.now();

    public CinemaResponse convertToDTO() {
        return CinemaResponse.builder()
                .id(this.id)
                .name(this.name)
                .address(this.address)
                .district(this.district)
                .city(this.city)
                .phone(this.phone)
                .images(this.images)
                .build();
    }
}
