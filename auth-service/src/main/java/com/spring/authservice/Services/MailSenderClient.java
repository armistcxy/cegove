package com.spring.authservice.Services;

import com.spring.authservice.DTOs.MailRequest;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.util.Arrays;

@Service
public class MailSenderClient {

    private final WebClient webClient;
    private static final String MAIL_SEND_ENDPOINT = "/v1/notifications/send";

    public MailSenderClient() {
        this.webClient = WebClient.builder()
                .baseUrl("https://notification.cegove.cloud")
                .build();
    }

    /**
     * Gửi email OTP lấy lại mật khẩu.
     * @param recipientEmail Địa chỉ email của người nhận.
     * @param otpCode Mã OTP.
     * @return Mono<Boolean> - Trả về true nếu gửi thành công, false nếu thất bại.
     */
    public Mono<Boolean> sendPasswordResetOTP(String recipientEmail, String otpCode) {
        String htmlBody = createOtpEmailBody(otpCode);

        MailRequest request = MailRequest.builder()
                .to(Arrays.asList(recipientEmail))
                .subject("Yêu cầu đặt lại mật khẩu của bạn")
                .body(htmlBody).build();

        return webClient.post()
                .uri(MAIL_SEND_ENDPOINT)
                .bodyValue(request)
                .retrieve()
                .onStatus(status -> status.is4xxClientError() || status.is5xxServerError(),
                        response -> response.bodyToMono(String.class)
                                .flatMap(errorBody -> Mono.error(new RuntimeException("API Error: " + errorBody))))
                .bodyToMono(Void.class)
                .thenReturn(true)
                .onErrorResume(WebClientResponseException.class, e -> {
                    System.err.println("WebClient Error for OTP: " + e.getMessage());
                    return Mono.just(false);
                })
                .onErrorResume(e -> {
                    System.err.println("General Error during OTP send: " + e.getMessage());
                    return Mono.just(false);
                });
    }

    /**
     * Tạo chuỗi HTML cho nội dung email OTP.
     */
    private String createOtpEmailBody(String otpCode) {
        return String.format("""
            <div style="font-family: Arial, sans-serif; padding: 20px; text-align: center; border: 1px solid #ddd; max-width: 500px; margin: auto;">
                <h2 style="color: #c90000;">Mã Đăng Nhập</h2>
                <p>Đây là mã đăng nhập (OTP) của bạn để đặt lại mật khẩu:</p>
                <div style="font-size: 36px; font-weight: bold; letter-spacing: 5px; margin: 30px 0; padding: 10px; border: 2px dashed #c90000;">
                    %s
                </div>
                <p style="color: #888;">Mã này sẽ sớm hết hạn. Vui lòng sử dụng ngay.</p>
            </div>
            """, otpCode);
    }
}