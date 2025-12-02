// MovieLogic.ts

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

const API_URL =
  "https://movies.cegove.cloud/api/v1/movies/?page=1&page_size=20&sort_order=desc";

export async function fetchMovies(): Promise<Movie[]> {
  try {
    const res = await fetch(API_URL);
    const json = await res.json();
    return json.items ?? [];
  } catch (error) {
    console.error("Fetch movies failed:", error);
    return [];
  }
}
