package com.spring.authservice.OAuth2;

import com.spring.authservice.Enums.Provider;
import com.spring.authservice.Enums.UserRole;
import com.spring.authservice.Models.User;
import com.spring.authservice.Reposistories.UserReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class OAuth2Service implements OAuth2UserService<OAuth2UserRequest, OAuth2User> {
    @Autowired
    private UserReposistory reposistory;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2UserService<OAuth2UserRequest, OAuth2User> delegate = new DefaultOAuth2UserService();
        OAuth2User oAuth2User = delegate.loadUser(userRequest);

        String providerId = userRequest.getClientRegistration().getRegistrationId();

        String email = oAuth2User.getAttribute("email");
        Optional<User> userOptional = reposistory.findByEmail(email);

        User user;
        if (userOptional.isEmpty()) {
            user = new User();
            user.setRole(UserRole.USER);
            user.setEmail(email);

            if (providerId.equalsIgnoreCase("google")) {
                user.setImg(oAuth2User.getAttribute("picture"));
                user.setFullName(oAuth2User.getAttribute("name"));
                user.setProvider(Provider.GOOGLE);
            } else {
                throw new OAuth2AuthenticationException("Login with " + providerId + " is not supported");
            }

        } else {
            user = userOptional.get();
            if (!user.getProvider().equals(Provider.GOOGLE)) {
                throw new OAuth2AuthenticationException(new OAuth2Error("invalid_provider"),
                        "Tài khoản này đã không được đăng ký bằng Google. Vui lòng đăng nhập bằng phương thức khác.");
            }

        }
        reposistory.save(user);

        return oAuth2User;
    }
}