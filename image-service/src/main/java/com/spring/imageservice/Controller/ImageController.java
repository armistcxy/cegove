package com.spring.imageservice.Controller;

import com.spring.imageservice.Service.ImageService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/images")
public class ImageController {
    @Autowired
    private ImageService service;

    @Value("${internal.secret.key}")
    private String internalSecretKey;

    @PostMapping("")
    public ResponseEntity<?> uploadImage(@RequestParam("img") MultipartFile img, HttpServletRequest request) {
        try {
            if (!request.getHeader("X-Internal-Secret-key").equals(internalSecretKey)) {
                return ResponseEntity.status(403).body("Forbidden");
            }
            return ResponseEntity.ok(service.uploadImage(img));
        } catch (IOException e) {
            return ResponseEntity.status(400).body("Failed to parse image file.");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
