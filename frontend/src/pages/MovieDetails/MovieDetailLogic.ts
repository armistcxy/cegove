import type { Movie } from '../Movies/MovieLogic.ts';

const API_URL = "https://movies.cegove.cloud/api/v1/movies";
const RECOMMENDATION_API_URL = "https://recommendations.cegove.cloud/api/v1/recommendations";

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

export async function fetchSimilarMovies(id: string, limit: number = 20): Promise<Movie[]> {
  try {
    const res = await fetch(`${RECOMMENDATION_API_URL}/similar/${id}?limit=${limit}`);
    if (!res.ok) {
      throw new Error('Failed to fetch similar movies');
    }
    const data = await res.json();
    return data.recommendations || [];
  } catch (error) {
    console.error("Fetch similar movies failed:", error);
    return [];
  }
}