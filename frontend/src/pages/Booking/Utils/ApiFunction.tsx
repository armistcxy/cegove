import axios from 'axios';

export const api = axios.create({
    baseURL: 'https://booking.cegove.cloud/api/v1/showtimes',
});

export async function getShowtimeDetails(showtimeId: string) {
    return await api.get("/" + showtimeId);
}

export async function getShowtimeDetailsByDate(cinemaId: string, movieId: string, date: string) {
    return await api.get(``, {
        params: {
            'cinema_id': cinemaId,
            'movie_id': movieId,
            'date': date
        }
    });
}

export async function getShowtimeSeats(showtimeId: string) {
    return await api.get(`/${showtimeId}/seats`);
}