import axios from 'axios';

export async function addCinema(cinema: {
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
}) {
  const token = localStorage.getItem('access-token') || '';
  const formData = new FormData();
  formData.append('name', cinema.name);
  formData.append('address', cinema.address);
  formData.append('city', cinema.city);
  formData.append('district', cinema.district);
  formData.append('phone', cinema.phone);
  const res = await axios.post('https://cinema.cegove.cloud/cinemas', formData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'multipart/form-data'
    }
  });
  return res.data;
}

export async function deleteCinema(id: number) {
  const token = localStorage.getItem('access-token') || '';
  await axios.delete(`https://cinema.cegove.cloud/cinemas/${id}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}

export async function updateCinema(id: number, cinema: {
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
}) {
  const token = localStorage.getItem('access-token') || '';
  const formData = new FormData();
  formData.append('name', cinema.name);
  formData.append('address', cinema.address);
  formData.append('city', cinema.city);
  formData.append('district', cinema.district);
  formData.append('phone', cinema.phone);
  const res = await axios.put(`https://cinema.cegove.cloud/cinemas/${id}`, formData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'multipart/form-data'
    }
  });
  return res.data;
}


export async function getRevenueByCinema(id: number, month: number, year: number) {
    const token = localStorage.getItem('access-token') || '';
    const res = await axios.get(`https://cinema.cegove.cloud/cinemas/${id}/revenue?month=${month}&year=${year}`, {
      headers: {
        'Authorization': `Bearer ${token}`
        }
    });
    return res.data;
}