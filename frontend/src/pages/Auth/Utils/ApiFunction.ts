import axios from 'axios';
import type {LoginForm, RegistrationForm} from "./Type.ts";

export const api = axios.create({
    baseURL: 'http://localhost:3002',
});

export async function register(registrationData:RegistrationForm) {
    return await api.post('/auth/register', registrationData);
}

export async function login(loginData:LoginForm) {
    return await api.post('/auth/login', loginData);
}

export async function logout(token:string) {
    return await api.post('/auth/logout', {}, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}