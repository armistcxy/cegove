import axios from 'axios';

export async function fetchTotalUsers(token: string): Promise<number> {
  const res = await axios.get('https://user.cegove.cloud/users', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return Array.isArray(res.data) ? res.data.length : 0;
}
