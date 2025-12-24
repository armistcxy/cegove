import type { Auditorium } from "../../Cinemas/CinemaLogic";

export async function fetchAuditoriumsByCinemaId(cinemaId: number): Promise<Auditorium[]> {
  const token = localStorage.getItem('access-token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const response = await fetch(`https://cinema.cegove.cloud/cinemas/${cinemaId}/auditoriums`, { headers });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

export async function addAuditorium(cinemaId: number, name: string, pattern: string) {
  const token = localStorage.getItem('access-token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const body = JSON.stringify({ name, pattern });
  const response = await fetch(`https://cinema.cegove.cloud/cinemas/${cinemaId}/auditoriums`, {
    method: 'POST', headers, body
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

export async function updateAuditoriumPattern(auditoriumId: number, pattern: string) {
  const token = localStorage.getItem('access-token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const body = JSON.stringify({ pattern });
  const response = await fetch(`https://cinema.cegove.cloud/auditoriums/${auditoriumId}`, {
    method: 'PUT', headers, body
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

export async function deleteAuditorium(auditoriumId: number) {
  const token = localStorage.getItem('access-token');
  const headers: HeadersInit = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const response = await fetch(`https://cinema.cegove.cloud/auditoriums/${auditoriumId}`, {
    method: 'DELETE', headers
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return true;
}
