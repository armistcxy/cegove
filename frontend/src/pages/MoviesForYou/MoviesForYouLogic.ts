import type { Movie } from '../Movies/MovieLogic.ts';
import { fetchMovies } from '../Movies/MovieLogic.ts';

const RECOMMENDATION_API_URL = "https://recommendations.cegove.cloud/api/v1/collaborative";

export interface PersonalizedRequest {
  user_id: number;
  top_n?: number;
  collaborative_weight?: number;
  exclude_watched?: boolean;
}

export interface PersonalizedResponse {
  recommendations: Movie[];
  total: number;
  method: string;
  user_id: number;
  collaborative_weight: number;
  exclude_watched: boolean;
}

export async function fetchPersonalizedMovies(
  userId: number,
  topN: number = 20,
  collaborativeWeight: number = 0.7,
  excludeWatched: boolean = true
): Promise<PersonalizedResponse | null> {
  try {
    const token = localStorage.getItem('access-token');
    
    const requestBody: PersonalizedRequest = {
      user_id: userId,
      top_n: topN,
      collaborative_weight: collaborativeWeight,
      exclude_watched: excludeWatched
    };

    const headers: HeadersInit = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${RECOMMENDATION_API_URL}/personalized`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody)
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      
      // Nếu model chưa được train, fallback sang phim phổ biến
      if (res.status === 400 || errorData.detail?.includes('chưa được train')) {
        console.log('Model chưa train, fallback sang phim phổ biến');
        const fallbackMovies = await fetchMovies(1, topN, { sort_by: 'votes_desc' });
        return {
          recommendations: fallbackMovies.items,
          total: fallbackMovies.items.length,
          method: 'fallback-popular',
          user_id: userId,
          collaborative_weight: 0,
          exclude_watched: false
        };
      }
      
      throw new Error('Failed to fetch personalized movies');
    }

    const data: PersonalizedResponse = await res.json();
    return data;
  } catch (error) {
    console.error("Fetch personalized movies failed:", error);
    
    // Fallback: trả về phim có rating cao
    try {
      const fallbackMovies = await fetchMovies(1, topN, { sort_by: 'votes_desc', min_rating: 7 });
      return {
        recommendations: fallbackMovies.items,
        total: fallbackMovies.items.length,
        method: 'fallback-popular',
        user_id: userId,
        collaborative_weight: 0,
        exclude_watched: false
      };
    } catch (fallbackError) {
      console.error("Fallback also failed:", fallbackError);
      return null;
    }
  }
}
