export interface RegistrationForm {
    fullName: string;
    email: string;
    phone: string;
    password: string;
    dob: string;
    address: string;
    district: string;
    city: string;
    gender: "MALE" | "FEMALE" | "OTHER";
    img: File | null;
}

export interface LoginForm {
    username: string;
    password: string;
}

export interface VerifyOtpForm {
    email: string;
    otp: string;
}

export interface ChangePasswordForm {
    email: string;
    otp: string;
    newPassword: string;
    confirmNewPassword: string;
}

