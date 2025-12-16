import axios from 'axios';

export const adminApi = axios.create({
    baseURL: 'https://user.cegove.cloud/users',
});

export async function getAllUsers(token: string) {
    return await adminApi.get('', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}

export async function deleteUser(token: string, userId: number) {
    return await adminApi.delete(`/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
}

export async function setUserRole(token: string, userId: number, role: string) {
    return await adminApi.put(`/${userId}/role`, role, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'text/plain'
        }
    });
}
