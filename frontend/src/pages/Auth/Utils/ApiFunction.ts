import axios from 'axios';
import type {LoginForm, RegistrationForm, VerifyOtpForm, ChangePasswordForm} from "./Type.ts";

export const api = axios.create({
    baseURL: 'https://auth.cegove.cloud/auth',
});

export async function register(registrationData:RegistrationForm) {
    const form = new FormData();
    form.append('fullName', registrationData.fullName);
    form.append('email', registrationData.email);
    form.append('phone', registrationData.phone);
    form.append('password', registrationData.password);
    form.append('dob', registrationData.dob);
    form.append('address', registrationData.address);
    form.append('district', registrationData.district);
    form.append('city', registrationData.city);
    form.append('gender', registrationData.gender);
    if (registrationData.img) {
        form.append('img', registrationData.img);
    }
    return await api.post('/register', form);
}

export async function login(loginData:LoginForm) {
    return await api.post('/login', loginData);
}

export async function logout(token:string) {
    return await api.post('/logout', {}, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}

export async function sendOtp(verifyOtpForm: VerifyOtpForm) {
    return await api.post('/reset-password-otp', verifyOtpForm);
}

export async function verifyOtp(verifyOtpForm: VerifyOtpForm) {
    return await api.post('/otp-verify', verifyOtpForm);
}

export async function resetPassword(changePasswordForm: ChangePasswordForm) {
    return await api.post('/forgot-password-change', changePasswordForm);
}