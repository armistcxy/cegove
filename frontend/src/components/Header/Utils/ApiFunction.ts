import axios from 'axios';

export const api = axios.create({
    baseURL: 'http://localhost:3003',
});

export async function getUserProfile(token: string) {
    return await api.get('/users/profile', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}