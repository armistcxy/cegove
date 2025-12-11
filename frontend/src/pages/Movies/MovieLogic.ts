
export interface Movie {
  id: number;
  poster_link: string;
  series_title: string;
  released_year: string;
  certificate: string;
  runtime: string;
  genre: string;
  imdb_rating: number;
  overview: string;
  director: string;
  star1: string;
  star2: string;
  star3: string;
  star4: string;
}

export interface MoviesResponse {
  items: Movie[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const BASE_API_URL = "https://movies.cegove.cloud/api/v1/movies/";

export interface MovieFilters {
  genre?: string;
  min_rating?: number;
  sort_by?: 'votes_asc' | 'votes_desc';
}

export async function fetchMovies(
  page: number = 1, 
  pageSize: number = 24, 
  filters?: MovieFilters
): Promise<MoviesResponse> {
  try {
    let API_URL = `${BASE_API_URL}?page=${page}&page_size=${pageSize}&sort_order=desc`;
    
    // Add filters to URL if provided
    if (filters?.genre) {
      API_URL += `&genre=${encodeURIComponent(filters.genre)}`;
    }
    if (filters?.min_rating !== undefined) {
      API_URL += `&min_rating=${filters.min_rating}`;
    }
    if (filters?.sort_by) {
      // Convert to API format: votes_asc -> asc, votes_desc -> desc
      const sortOrder = filters.sort_by === 'votes_asc' ? 'asc' : 'desc';
      API_URL += `&sort_by=no_of_votes&sort_order=${sortOrder}`;
    }
    
    const res = await fetch(API_URL);
    const json = await res.json();
    return {
      items: json.items ?? [],
      total: json.total ?? 0,
      page: json.page ?? page,
      page_size: json.page_size ?? pageSize,
      total_pages: json.total_pages ?? 0
    };
  } catch (error) {
    console.error("Fetch movies failed:", error);
    return {
      items: [],
      total: 0,
      page: page,
      page_size: pageSize,
      total_pages: 0
    };
  }
}

export async function fetchGenres(): Promise<string[]> {
  try {
    const API_URL = `${BASE_API_URL}stats/by-genre`;
    const token = localStorage.getItem('access-token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const res = await fetch(API_URL, { headers });
    const json = await res.json();
    // Extract genre names from the stats response
    const genres = json.map((item: { genre: string; count: number }) => item.genre);
    return genres ?? [];
  } catch (error) {
    console.error("Fetch genres failed:", error);
    return [];
  }
}
