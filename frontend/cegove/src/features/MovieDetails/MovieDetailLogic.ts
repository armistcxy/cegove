import type { Movie } from '../Movies/MovieLogic';

const API_URL = "https://movies.cegove.cloud/api/v1/movies";

export async function fetchMovieDetail(id: string): Promise<Movie | null> {
  try {
    const res = await fetch(`${API_URL}/${id}`);
    if (!res.ok) {
      throw new Error('Movie not found');
    }
    const movie = await res.json();
    return movie;
  } catch (error) {
    console.error("Fetch movie detail failed:", error);
    return null;
  }
}