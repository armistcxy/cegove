const API_BASE_URL = 'https://cinema.cegove.cloud';

export interface Cinema {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
  email: string;
}

export async function fetchCinemas(city?: string): Promise<Cinema[]> {
  try {
    const url = city 
      ? `${API_BASE_URL}/cinemas?city=${encodeURIComponent(city)}`
      : `${API_BASE_URL}/cinemas`;
    
    const token = localStorage.getItem('access-token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching cinemas:', error);
    throw error;
  }
}

export async function fetchCinemaById(id: number): Promise<Cinema> {
  try {
    const token = localStorage.getItem('access-token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/cinemas/${id}`, { headers });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching cinema:', error);
    throw error;
  }
}

export async function fetchCities(): Promise<string[]> {
  try {
    const cinemas = await fetchCinemas();
    // Extract unique cities from all cinemas
    const uniqueCities = [...new Set(cinemas.map(cinema => cinema.city))];
    return uniqueCities.sort();
  } catch (error) {
    console.error('Error fetching cities:', error);
    return [];
  }
}
