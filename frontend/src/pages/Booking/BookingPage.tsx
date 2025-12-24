import React, { useState, useEffect } from "react";
import {getShowtimeDetails, getShowtimeSeats} from "./Utils/ApiFunction.tsx";
import {type Auditorium, type Cinema, fetchAuditorium, fetchCinemaById} from "../Cinemas/CinemaLogic.ts";
import {fetchMovieDetail} from "../MovieDetails/MovieDetailLogic.ts";
import type {Showtime} from "./Utils/Type.ts";
import type {Movie} from "../Movies/MovieLogic.ts";
import {useUser} from "../../context/UserContext.tsx";
import axios from "axios";

const BookingPage = ({ showtimeId }) => {
    const { userProfile } = useUser();
    const [step, setStep] = useState<1 | 2>(1);

    const [showtime, setShowtime] = useState<Showtime | null>(null);
    const [movie, setMovie] = useState<Movie | null>(null);
    const [cinema, setCinema] = useState<Cinema | null>(null);
    const [auditorium, setAuditorium] = useState<Auditorium | null>(null);
    const [seats, setSeats] = useState([]);
    const [selectedSeats, setSelectedSeats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [paymentProcessing, setPaymentProcessing] = useState(false);

    // Fetch showtime and related data
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                // Fetch showtime details
                const showtimeResponse = await getShowtimeDetails(showtimeId);
                const showtimeData = showtimeResponse.data;
                setShowtime(showtimeData);

                // Fetch movie details
                const movieData = await fetchMovieDetail(showtimeData.movie_id);
                setMovie(movieData);

                // Fetch cinema details
                const cinemaData = await fetchCinemaById(showtimeData.cinema_id);
                setCinema(cinemaData);

                // Fetch auditorium details
                const auditoriumData = await fetchAuditorium(showtimeData.auditorium_id);
                setAuditorium(auditoriumData);

                // Fetch booked seats for this showtime
                const seatsResponse = await getShowtimeSeats(showtimeId);
                const seatsData = await seatsResponse.data;

                processSeats(auditoriumData.pattern, seatsData);
            } catch (err) {
                console.error("Error fetching data:", err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (showtimeId) {
            fetchData();
        }
    }, [showtimeId]);

    // Process seats based on pattern and API data
    const processSeats = (pattern, apiSeatsData) => {
        const seatData = [];
        let rows = [];

        if (pattern === "ONE") {
            rows = [
                { row: "A", count: 19, type: "normal", isCouple: false },
                { row: "B", count: 19, type: "normal", isCouple: false },
                { row: "C", count: 19, type: "normal", isCouple: false },
                { row: "D", count: 19, type: "vip", isCouple: false },
                { row: "E", count: 19, type: "vip", isCouple: false },
                { row: "F", count: 19, type: "vip", isCouple: false },
                { row: "G", count: 19, type: "vip", isCouple: false },
                { row: "H", count: 19, type: "vip", isCouple: false },
                { row: "K", count: 7, type: "sweetbox", isCouple: true }
            ];
        } else if (pattern === "TWO") {
            rows = [
                { row: "A", count: 26, type: "normal", isCouple: false },
                { row: "B", count: 26, type: "normal", isCouple: false },
                { row: "C", count: 26, type: "normal", isCouple: false },
                { row: "D", count: 26, type: "vip", isCouple: false },
                { row: "E", count: 26, type: "vip", isCouple: false },
                { row: "F", count: 26, type: "vip", isCouple: false },
                { row: "G", count: 26, type: "vip", isCouple: false },
                { row: "H", count: 26, type: "vip", isCouple: false },
                { row: "I", count: 26, type: "vip", isCouple: false },
                { row: "J", count: 26, type: "vip", isCouple: false },
                { row: "K", count: 26, type: "vip", isCouple: false },
                { row: "L", count: 13, type: "sweetbox", isCouple: true }
            ];
        } else if (pattern === "THREE") {
            rows = [
                { row: "A", count: 10, type: "normal", isCouple: false },
                { row: "B", count: 10, type: "normal", isCouple: false },
                { row: "C", count: 10, type: "normal", isCouple: false },
                { row: "D", count: 10, type: "vip", isCouple: false },
                { row: "E", count: 10, type: "vip", isCouple: false },
                { row: "F", count: 10, type: "vip", isCouple: false },
                { row: "G", count: 10, type: "vip", isCouple: false },
                { row: "H", count: 10, type: "vip", isCouple: false },
                { row: "I", count: 10, type: "vip", isCouple: false },
                { row: "J", count: 10, type: "vip", isCouple: false },
                { row: "K", count: 5, type: "sweetbox", isCouple: true }
            ];
        }

        // Create a map for quick lookup of API seat data
        const apiSeatMap = {};
        apiSeatsData.forEach(seat => {
            apiSeatMap[seat.seat_number] = seat;
        });

        rows.forEach(({ row, count, type, isCouple }) => {
            if (isCouple) {
                for (let col = 1; col <= count; col++) {
                    const seatNumber = `${row}${col}`;
                    const apiSeat = apiSeatMap[seatNumber];

                    seatData.push({
                        id: seatNumber,
                        row,
                        col,
                        type: apiSeat?.seat_type?.toLowerCase() || type,
                        isCouple: true,
                        status: apiSeat?.status !== 0 ? "booked" : "available",
                        price: apiSeat?.price || 0,
                        seat_id: apiSeat?.seat_id
                    });
                }
            } else {
                for (let col = 1; col <= count; col++) {
                    const seatNumber = `${row}${col}`;
                    const apiSeat = apiSeatMap[seatNumber];

                    seatData.push({
                        id: seatNumber,
                        row,
                        col,
                        type: apiSeat?.seat_type?.toLowerCase() || type,
                        isCouple: false,
                        status: apiSeat?.status !== 0 ? "booked" : "available",
                        price: apiSeat?.price || 0,
                        seat_id: apiSeat?.seat_id
                    });
                }
            }
        });

        setSeats(seatData);
    };

    const handleSeatClick = (seat) => {
        if (seat.status === "booked") return;

        if (selectedSeats.includes(seat.id)) {
            setSelectedSeats(selectedSeats.filter(s => s !== seat.id));
        } else {
            setSelectedSeats([...selectedSeats, seat.id]);
        }
    };

    const getSeatClass = (seat) => {
        const baseClass = "text-xs font-bold rounded cursor-pointer transition-all duration-200 flex items-center justify-center border-2";
        const sizeClass = seat.isCouple ? "w-16 h-8" : "w-8 h-8";

        if (seat.status === "booked") {
            return `${baseClass} ${sizeClass} bg-gray-400 border-gray-500 text-white cursor-not-allowed`;
        }

        if (selectedSeats.includes(seat.id)) {
            return `${baseClass} ${sizeClass} bg-red-800 border-red-900 text-white scale-110`;
        }

        // Map seat_type from API to colors
        const seatType = seat.type.toLowerCase();
        if (seatType === "standard" || seatType === "normal") {
            return `${baseClass} ${sizeClass} bg-emerald-100 border-emerald-400 text-emerald-800 hover:bg-emerald-200`;
        } else if (seatType === "vip") {
            return `${baseClass} ${sizeClass} bg-orange-100 border-orange-400 text-orange-800 hover:bg-orange-200`;
        } else if (seatType === "sweetbox" || seatType === "couple") {
            return `${baseClass} ${sizeClass} bg-pink-300 border-pink-500 text-white hover:bg-pink-400`;
        }

        // Default
        return `${baseClass} ${sizeClass} bg-gray-100 border-gray-400 text-gray-800 hover:bg-gray-200`;
    };

    const calculateTotal = () => {
        // Calculate total based on actual seat prices from API
        let total = 0;
        selectedSeats.forEach(seatId => {
            const seat = seats.find(s => s.id === seatId);
            if (seat) {
                total += seat.price || 0;
            }
        });
        return total;
    };

    const formatDateTime = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const handleNext = () => {
        if (selectedSeats.length === 0) {
            alert("Vui lòng chọn ít nhất 1 ghế");
            return;
        }

        setStep(2);
    };

    const handleBackToSeats = () => {
        setStep(1);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-amber-50 flex items-center justify-center">
                <div className="text-2xl font-bold">Đang tải...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-amber-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="text-2xl font-bold text-red-600 mb-4">Có lỗi xảy ra</div>
                    <p className="text-gray-700">{error}</p>
                </div>
            </div>
        );
    }

    const getRowSeats = (row) => seats.filter(s => s.row === row);
    const uniqueRows = [...new Set(seats.map(s => s.row))];
    const availableSeats = seats.filter(s => s.status === "available").length;
    const totalSeats = seats.length;

    if (step === 1) {
        return (
            <div className="min-h-screen bg-amber-50 py-8">
                <div className="max-w-7xl mx-auto px-4">
                    {/* Header */}
                    <div className="bg-gray-900 text-white text-center py-4 rounded-t-lg">
                        <h1 className="text-2xl font-bold">BOOKING ONLINE</h1>
                    </div>

                    {/* Showtime Info */}
                    <div className="bg-amber-100 p-4 border-b-2 border-gray-300">
                        <h2 className="text-lg font-bold">
                            {cinema?.name || "Cinema"} | {auditorium?.name || "Auditorium"} | Số ghế ({availableSeats}/{totalSeats})
                        </h2>
                        <p className="text-sm text-gray-700">
                            {showtime && formatDateTime(showtime.start_time)} ~ {showtime && formatDateTime(showtime.end_time)}
                        </p>
                    </div>

                    {/* Legend */}
                    <div className="bg-gray-200 py-3 text-center">
                        <span className="font-bold text-gray-800">Người / Ghế</span>
                    </div>

                    {/* Screen */}
                    <div className="bg-white py-8">
                        <div className="max-w-5xl mx-auto">
                            <div className="relative mb-8">
                                <svg viewBox="0 0 800 100" className="w-full">
                                    <path
                                        d="M 50 80 Q 400 20 750 80"
                                        fill="none"
                                        stroke="#999"
                                        strokeWidth="3"
                                    />
                                    <text x="400" y="50" textAnchor="middle" fill="#666" fontSize="24" fontWeight="bold">
                                        SCREEN
                                    </text>
                                </svg>
                            </div>

                            {/* Seats Grid */}
                            <div className="flex flex-col items-center gap-2">
                                {uniqueRows.map(row => {
                                    const rowSeats = getRowSeats(row);
                                    return (
                                        <div key={row} className="flex items-center gap-2">
                                            <span className="w-8 text-center font-bold text-gray-700">{row}</span>
                                            <div className="flex gap-1">
                                                {rowSeats.map(seat => (
                                                    <button
                                                        key={seat.id}
                                                        onClick={() => handleSeatClick(seat)}
                                                        className={getSeatClass(seat)}
                                                        disabled={seat.status === "booked"}
                                                    >
                                                        {seat.col}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Legend Info */}
                            <div className="mt-8 grid grid-cols-2 md:grid-cols-5 gap-4 max-w-3xl mx-auto">
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 bg-red-800 border-2 border-red-900 rounded"></div>
                                    <span className="text-sm">Checked</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 bg-emerald-100 border-2 border-emerald-400 rounded"></div>
                                    <span className="text-sm">Thường</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 bg-gray-400 border-2 border-gray-500 rounded"></div>
                                    <span className="text-sm">Đã chọn</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 bg-orange-100 border-2 border-orange-400 rounded"></div>
                                    <span className="text-sm">VIP</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-12 h-6 bg-pink-300 border-2 border-pink-500 rounded"></div>
                                    <span className="text-sm">Sweetbox (Couple)</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    {/* Footer */}
                    <div className="bg-gray-900 text-white p-4 rounded-b-lg">
                        <div className="flex flex-wrap items-center justify-between gap-4">
                            <div className="flex items-center gap-6 flex-1">
                                {/* Movie Poster */}
                                <div className="flex-shrink-0">
                                    <img
                                        src={movie?.poster_link || "/placeholder-poster.jpg"}
                                        alt={movie?.series_title || "Movie"}
                                        className="w-20 h-28 object-cover rounded shadow-lg"
                                        onError={(e) => {
                                            e.target.src = "/placeholder-poster.jpg";
                                        }}
                                    />
                                </div>

                                <div>
                                    <p className="font-bold text-lg">{movie?.series_title || "Movie Title"}</p>
                                    <p className="text-sm">2D - P</p>
                                </div>

                                <div>
                                    <p className="text-sm text-gray-400">Rạp</p>
                                    <p className="font-bold">{cinema?.name || "Cinema"}</p>
                                    <p>{showtime && formatDateTime(showtime.start_time)}</p>
                                    <p>{auditorium?.name || "Auditorium"}</p>
                                </div>

                                <div>
                                    <p className="text-sm text-gray-400">Ghế đã chọn</p>
                                    <p className="font-bold">{selectedSeats.length > 0 ? selectedSeats.join(", ") : "Chưa chọn"}</p>
                                </div>

                                <div className="text-right ml-auto">
                                    <p className="text-sm text-gray-400">Tổng tiền</p>
                                    <p className="font-bold text-2xl text-yellow-400">{calculateTotal().toLocaleString()} đ</p>
                                </div>
                            </div>

                            <button
                                onClick={handleNext}
                                disabled={selectedSeats.length === 0}
                                className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-8 py-3 rounded-lg font-bold transition"
                            >
                                THANH TOÁN
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-amber-50 py-8">
            <div className="max-w-4xl mx-auto px-4">
                {/* Header */}
                <div className="bg-gray-900 text-white text-center py-4 rounded-t-lg">
                    <h1 className="text-2xl font-bold">THANH TOÁN</h1>
                </div>

                <div className="bg-white p-8 rounded-b-lg shadow-lg">
                    {/* Thông tin đặt vé */}
                    <div className="mb-8">
                        <h2 className="text-xl font-bold mb-4 text-gray-800">Thông tin đặt vé</h2>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="flex gap-4">
                                <img
                                    src={movie?.poster_link || "/placeholder-poster.jpg"}
                                    alt={movie?.series_title || "Movie"}
                                    className="w-32 h-44 object-cover rounded shadow"
                                />
                                <div>
                                    <p className="font-bold text-lg mb-2">{movie?.series_title}</p>
                                    <p className="text-sm text-gray-600">2D - P</p>
                                    <p className="text-sm text-gray-600 mt-4">
                                        <span className="font-semibold">Rạp:</span> {cinema?.name}
                                    </p>
                                    <p className="text-sm text-gray-600">
                                        <span className="font-semibold">Phòng:</span> {auditorium?.name}
                                    </p>
                                    <p className="text-sm text-gray-600">
                                        <span className="font-semibold">Suất chiếu:</span> {showtime && formatDateTime(showtime.start_time)}
                                    </p>
                                </div>
                            </div>

                            <div className="border-l-2 border-gray-200 pl-6">
                                <h3 className="font-bold mb-3">Chi tiết</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Ghế:</span>
                                        <span className="font-semibold">{selectedSeats.join(", ")}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Số lượng:</span>
                                        <span className="font-semibold">{selectedSeats.length} ghế</span>
                                    </div>
                                    <div className="border-t pt-2 mt-4">
                                        <div className="flex justify-between text-lg">
                                            <span className="font-bold">Tổng tiền:</span>
                                            <span className="font-bold text-red-600">{calculateTotal().toLocaleString()} đ</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Phương thức thanh toán */}
                    <div className="mb-8">
                        <h2 className="text-xl font-bold mb-4 text-gray-800">Phương thức thanh toán</h2>

                        <div className="max-w-md mx-auto">
                            <button className="w-full border-2 border-blue-500 bg-blue-50 hover:bg-blue-100 rounded-lg p-6 transition">
                                <div className="flex items-center justify-center gap-4">
                                    <img
                                        src="https://vinadesign.vn/uploads/images/2023/05/vnpay-logo-vinadesign-25-12-57-55.jpg"
                                        alt="VNPay"
                                        className="h-12"
                                    />
                                    <div className="text-left">
                                        <p className="font-bold text-lg">Thanh toán qua VNPay</p>
                                        <p className="text-sm text-gray-600">Thanh toán bằng QR Code hoặc ứng dụng VNPay</p>
                                    </div>
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Buttons */}
                    <div className="flex justify-between gap-4">
                        <button
                            onClick={handleBackToSeats}
                            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold transition"
                        >
                            ← Quay lại chọn ghế
                        </button>
                        <button
                            onClick={async () => {
                                if (!userProfile?.id) {
                                    alert("Vui lòng đăng nhập để tiếp tục thanh toán");
                                    return;
                                }

                                try {
                                    setPaymentProcessing(true);

                                    // Get selected seat IDs and convert to strings
                                    const seatIds = selectedSeats.map(seatId => {
                                        const seat = seats.find(s => s.id === seatId);
                                        return seat?.seat_id ? String(seat.seat_id) : null;
                                    }).filter(Boolean);

                                    const bookingData = {
                                        user_id: String(userProfile.id),
                                        showtime_id: String(showtimeId),
                                        seat_ids: seatIds
                                    };

                                    console.log("Creating booking with data:", bookingData);

                                    // Create booking
                                    const bookingResponse = await axios.post(
                                        "https://booking.cegove.cloud/api/v1/bookings",
                                        bookingData
                                    );

                                    const { payment } = bookingResponse.data;

                                    // Redirect to payment URL
                                    if (payment?.url) {
                                        window.location.href = payment.url;
                                    } else {
                                        throw new Error("Không nhận được URL thanh toán");
                                    }
                                } catch (err) {
                                    console.error("Payment error:", err);
                                    console.error("Error response:", err.response?.data);

                                    let errorMessage = "Có lỗi xảy ra khi xử lý thanh toán";
                                    if (err.response?.data?.detail) {
                                        errorMessage += ": " + err.response.data.detail;
                                    } else if (err.response?.data?.message) {
                                        errorMessage += ": " + err.response.data.message;
                                    } else if (err.message) {
                                        errorMessage += ": " + err.message;
                                    }

                                    alert(errorMessage);
                                    setPaymentProcessing(false);
                                }
                            }}
                            disabled={paymentProcessing}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-500 text-white px-8 py-3 rounded-lg font-bold transition"
                        >
                            {paymentProcessing ? "Đang xử lý..." : "Thanh toán"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BookingPage;