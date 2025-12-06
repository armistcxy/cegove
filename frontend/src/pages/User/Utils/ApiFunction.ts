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

export async function updateUserProfile(token: string, formData: FormData) {
    return await api.put('/profile', formData, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
        }
    });
}