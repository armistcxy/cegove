import axios from 'axios';

export const api = axios.create({
    baseURL: 'https://user.cegove.cloud/users',
});

export async function getUserProfile(token: string) {
    return await api.get('/profile', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}