import type { Movie } from "../Movies/MovieLogic";

export async function fetchRecentMovies(): Promise<Movie[]> {
  // Gọi API lấy 54 phim mới nhất theo released_year
  const API_URL = "https://movies.cegove.cloud/api/v1/movies/?page=1&page_size=54&sort_by=released_year&sort_order=desc";
  const res = await fetch(API_URL, { headers: { 'accept': 'application/json' } });
  const json = await res.json();
  return json.items ?? [];
}
