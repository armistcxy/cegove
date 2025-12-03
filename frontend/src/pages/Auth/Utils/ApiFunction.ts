import axios from 'axios';
import type {LoginForm, RegistrationForm} from "./Type.ts";

export const api = axios.create({
    baseURL: 'https://auth.cegove.cloud/auth',
});

export async function register(registrationData:RegistrationForm) {
    return await api.post('/register', registrationData);
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