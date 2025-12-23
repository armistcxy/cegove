package com.spring.authservice.OAuth2;

import com.spring.authservice.Models.User;
import com.spring.authservice.Reposistories.UserReposistory;
import com.spring.authservice.Services.JwtService;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.DefaultRedirectStrategy;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;

import java.io.IOException;

@Component
public class OAuth2SuccessHandler implements AuthenticationSuccessHandler {
    @Autowired
    private JwtService jwtService;

    @Autowired
    private UserReposistory reposistory;

    @Override
    public void onAuthenticationSuccess(
            HttpServletRequest request,
            HttpServletResponse response,
            Authentication authentication) throws IOException, ServletException {
        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();
        String email = oAuth2User.getAttribute("email");

        User user = reposistory.findByEmail(email).orElseThrow(() ->
                new RuntimeException("User not found after OAuth2 authentication"));

        String token = jwtService.generateToken(user);

        String feUrl = "https://demo.cegove.cloud/profile";
        String targetUrl = UriComponentsBuilder.fromUriString(feUrl)
                .queryParam("accessToken", token)
                .build().toUriString();

        new DefaultRedirectStrategy().sendRedirect(request, response, targetUrl);
    }
}
