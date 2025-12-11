export async function fetchTotalMovies(): Promise<number> {
  try {
    const res = await fetch('https://movies.cegove.cloud/api/v1/movies/?page=1&page_size=1');
    const data = await res.json();
    return data.total || 0;
  } catch (error) {
    console.error('Error fetching total movies:', error);
    return 0;
  }
}

export async function fetchTotalCinemas(): Promise<number> {
  try {
    const res = await fetch('https://cinema.cegove.cloud/cinemas');
    const data = await res.json();
    return Array.isArray(data) ? data.length : 0;
  } catch (error) {
    console.error('Error fetching total cinemas:', error);
    return 0;
  }
}
