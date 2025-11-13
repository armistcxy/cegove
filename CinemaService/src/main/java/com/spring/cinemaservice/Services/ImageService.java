package com.spring.cinemaservice.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.util.UUID;

@Service
public class ImageService {
    @Autowired
    private S3Client s3Client;

    @Value("${digitalocean.spaces.bucket-name}")
    private String bucketName;

    /**
     * Upload image to DigitalOcean Spaces
     *
     * @param file the image file to upload
     */
    public String uploadImage(MultipartFile file) throws IOException {
        // Generate a unique file name
        String originalFileName = file.getOriginalFilename();
        String extension = "";
        if (originalFileName != null && originalFileName.contains(".")) {
            extension = originalFileName.substring(originalFileName.lastIndexOf("."));
        }
        String fileName = UUID.randomUUID() + extension;

        // Create PutObjectRequest
        PutObjectRequest request = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(fileName)
                .acl("public-read")
                .contentType(file.getContentType())
                .build();

        // Upload the file
        s3Client.putObject(request, RequestBody.fromInputStream(
                file.getInputStream(),
                file.getSize()
        ));

        // Return the file URL
        return String.format("https://%s.%s.digitaloceanspaces.com/%s",
                bucketName,
                s3Client.serviceClientConfiguration().region().id(),
                fileName);
    }
}
