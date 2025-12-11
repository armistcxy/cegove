package com.spring.authservice.Exceptions;

public class UserAlreadyExistedException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public UserAlreadyExistedException(String message) {
        super(message);
    }
}
