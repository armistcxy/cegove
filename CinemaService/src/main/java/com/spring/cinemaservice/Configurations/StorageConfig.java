package com.spring.cinemaservice.Configurations;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;

@Configuration
public class StorageConfig {
    @Value("${digitalocean.spaces.access-key}")
    private String accessKey;

    @Value("${digitalocean.spaces.secret-key}")
    private String secretKey;

    @Value("${digitalocean.spaces.region}")
    private String region;

    @Value("${digitalocean.spaces.endpoint}")
    private String endpointUrl;

    @Bean
    public S3Client s3Client() {
        // 1. Tạo thông tin đăng nhập
        AwsBasicCredentials credentials = AwsBasicCredentials.create(accessKey, secretKey);
        StaticCredentialsProvider credentialsProvider = StaticCredentialsProvider.create(credentials);

        // 2. Cấu hình Region
        Region region = Region.of(this.region);

        // 3. Cấu hình Endpoint
        URI endpoint = URI.create(endpointUrl);

        return S3Client.builder()
                .credentialsProvider(credentialsProvider)
                .region(region)
                .endpointOverride(endpoint)
                .build();
    }
}
