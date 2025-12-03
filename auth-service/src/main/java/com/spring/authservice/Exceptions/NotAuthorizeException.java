package com.spring.authservice.Exceptions;

public class NotAuthorizeException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public NotAuthorizeException(String message) {
        super(message);
    }
}

