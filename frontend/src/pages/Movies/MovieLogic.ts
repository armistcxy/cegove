
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

export async function fetchMovies(page: number = 1, pageSize: number = 24): Promise<MoviesResponse> {
  try {
    const API_URL = `${BASE_API_URL}?page=${page}&page_size=${pageSize}&sort_order=desc`;
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
