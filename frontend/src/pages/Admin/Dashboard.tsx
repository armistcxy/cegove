import styles from './Admin.module.css';
import { useEffect, useState } from 'react';
import { fetchTotalMovies, fetchTotalCinemas } from './DashboardLogic';
import { fetchTotalUsers } from './Utils/UserApi';
import { type Cinema, fetchCinemas } from "../Cinemas/CinemaLogic.ts";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import {getRevenueByCinema} from "./Utils/CinemaApi.ts";

interface MonthlyRevenue {
    month: string;
    revenue: number;
}

// Custom Tooltip
const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: '#fff',
                padding: '12px 16px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
                <p style={{ margin: 0, fontWeight: 600, color: '#111827', marginBottom: 4 }}>
                    Tháng {payload[0].payload.month}
                </p>
                <p style={{ margin: 0, color: '#6366f1', fontWeight: 500 }}>
                    {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(payload[0].value)}
                </p>
            </div>
        );
    }
    return null;
};

export default function Dashboard() {
    const [totalMovies, setTotalMovies] = useState<number | null>(null);
    const [totalCinemas, setTotalCinemas] = useState<number | null>(null);
    const [totalUsers, setTotalUsers] = useState<number | null>(null);

    const [cinemas, setCinemas] = useState<Cinema[]>([]);
    const [selectedCinemaId, setSelectedCinemaId] = useState<number | null>(null);
    const [cities, setCities] = useState<string[]>([]);
    const [selectedCity, setSelectedCity] = useState<string>('');
    const [loadingCinemas, setLoadingCinemas] = useState(true);

    const [revenueData, setRevenueData] = useState<MonthlyRevenue[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchTotalMovies().then(setTotalMovies);
        fetchTotalCinemas().then(setTotalCinemas);
        const token = localStorage.getItem('access-token') || '';
        fetchTotalUsers(token).then(setTotalUsers);

        async function loadCinemas() {
            try {
                const cinemaList = await fetchCinemas();
                setCinemas(cinemaList);
                // Lấy danh sách thành phố từ cinemas
                const cityList = Array.from(new Set(cinemaList.map(c => c.city).filter(Boolean)));
                setCities(cityList);
            } catch (e) {
                setCinemas([]);
                setCities([]);
            } finally {
                setLoadingCinemas(false);
            }
        }

        loadCinemas();
    }, []);

    // Load revenue data khi chọn rạp
    useEffect(() => {
        if (selectedCinemaId) {
            setLoading(true);
            fetchYearlyRevenue(selectedCinemaId, 2025)
                .then(data => {
                    console.log(data);
                    setRevenueData(data);
                })
                .catch(error => {
                    console.error('Error loading revenue:', error);
                    setRevenueData([]);
                })
                .finally(() => {
                    setLoading(false);
                });
        } else {
            setRevenueData([]);
        }
    }, [selectedCinemaId]);

    const formatCurrency = (value: number) => {
        if (value >= 1_000_000) {
            return `${(value / 1_000_000).toFixed(1)}M`;
        } else if (value >= 1_000) {
            return `${(value / 1_000).toFixed(0)}K`;
        }
        return value.toString();
    };

    const fetchMonthlyRevenue = async (cinemaId: number, month: number, year: number): Promise<number> => {
        try {
            const response = await getRevenueByCinema(cinemaId, month, year);
            console.log(`${month}/${year}`, response);
            return response[0].revenue || 0;
        } catch (error) {
            console.error(`Error fetching revenue for cinema ${cinemaId}, month ${month}:`, error);
            return 0;
        }
    }

    const fetchYearlyRevenue = async (cinemaId: number, year: number): Promise<MonthlyRevenue[]> => {
        const months = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'];

        const revenuePromises = months.map(async (monthLabel, index) => {
            const revenue = await fetchMonthlyRevenue(cinemaId, index + 1, year);
            console.log(revenue);
            return {
                month: monthLabel,
                revenue
            };
        });

        return Promise.all(revenuePromises);
    }

    const selectedCinema = cinemas.find(c => c.id === selectedCinemaId);

    return (
        <div className={styles.pageContainer}>
            <h1 className={styles.pageTitle}>Dashboard</h1>
            <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                    </div>
                    <div className={styles.statInfo}>
                        <h3>Total Users</h3>
                        <p className={styles.statNumber}>{totalUsers !== null ? totalUsers : '...'}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                        </svg>
                    </div>
                    <div className={styles.statInfo}>
                        <h3>Total Movies</h3>
                        <p className={styles.statNumber}>{totalMovies !== null ? totalMovies : '...'}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="32" height="32">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                    </div>
                    <div className={styles.statInfo}>
                        <h3>Total Cinemas</h3>
                        <p className={styles.statNumber}>{totalCinemas !== null ? totalCinemas : '...'}</p>
                    </div>
                </div>
            </div>

            <div className={styles.section}>
                <h2 className={styles.sectionTitle}>Doanh thu theo tháng năm 2025</h2>

                <div className={styles.card} style={{ padding: '32px' }}>
                    {/* Filter Dropdowns */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 16,
                        marginBottom: 32,
                        flexWrap: 'wrap'
                    }}>
                        <label htmlFor="city-select" style={{ fontWeight: 500, color: '#374151' }}>
                            Chọn thành phố:
                        </label>
                        <select
                            id="city-select"
                            value={selectedCity}
                            onChange={e => {
                                setSelectedCity(e.target.value);
                                setSelectedCinemaId(null);
                            }}
                            style={{
                                padding: '8px 12px',
                                borderRadius: 6,
                                border: '1px solid #d1d5db',
                                minWidth: 180,
                                fontSize: 14,
                                cursor: 'pointer',
                                outline: 'none'
                            }}
                            disabled={loadingCinemas}
                        >
                            <option value="">-- Tất cả thành phố --</option>
                            {cities.map(city => (
                                <option key={city} value={city}>{city}</option>
                            ))}
                        </select>

                        <label htmlFor="cinema-select" style={{ fontWeight: 500, color: '#374151' }}>
                            Chọn rạp:
                        </label>
                        <select
                            id="cinema-select"
                            value={selectedCinemaId ?? ''}
                            onChange={e => setSelectedCinemaId(e.target.value ? Number(e.target.value) : null)}
                            style={{
                                padding: '8px 12px',
                                borderRadius: 6,
                                border: '1px solid #d1d5db',
                                minWidth: 250,
                                fontSize: 14,
                                cursor: 'pointer',
                                outline: 'none'
                            }}
                            disabled={loadingCinemas || (!selectedCity && cinemas.length > 10)}
                        >
                            <option value="">-- Chọn rạp --</option>
                            {cinemas
                                .filter(c => !selectedCity || c.city === selectedCity)
                                .map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                        </select>
                    </div>

                    {/* Chart or Empty State */}
                    {!selectedCinemaId ? (
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            minHeight: '400px'
                        }}>
                            <svg width="64" height="64" fill="none" stroke="#cbd5e1" strokeWidth="2" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                            <p style={{ fontSize: '18px', color: '#6b7280', marginTop: '20px', fontWeight: 500 }}>
                                Vui lòng chọn rạp để xem biểu đồ doanh thu
                            </p>
                            <p style={{ fontSize: '14px', color: '#9ca3af', marginTop: '8px' }}>
                                Chọn thành phố và rạp từ dropdown phía trên
                            </p>
                        </div>
                    ) : loading ? (
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            minHeight: '400px'
                        }}>
                            <svg width="48" height="48" fill="none" stroke="#bbb" strokeWidth="2" viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="10" strokeDasharray="4 2" />
                                <path d="M8 12h4l2 2m-2-2V8" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            <p style={{ fontSize: '16px', color: '#9ca3af', marginTop: '16px' }}>Đang tải dữ liệu...</p>
                        </div>
                    ) : (
                        <>
                            <div style={{ marginBottom: 20 }}>
                                <h3 style={{ fontSize: 18, fontWeight: 600, color: '#111827', margin: 0 }}>
                                    {selectedCinema?.name}
                                </h3>
                                <p style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>
                                    Tổng doanh thu năm: {new Intl.NumberFormat('vi-VN', {
                                    style: 'currency',
                                    currency: 'VND'
                                }).format(revenueData.reduce((sum, item) => sum + item.revenue, 0))}
                                </p>
                            </div>
                            <ResponsiveContainer width="100%" height={400}>
                                <BarChart data={revenueData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                    <XAxis
                                        dataKey="month"
                                        tick={{ fill: '#6b7280', fontSize: 12 }}
                                    />
                                    <YAxis
                                        tickCount={6}
                                        tickFormatter={formatCurrency}
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#6b7280', fontSize: 12 }}
                                    />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend
                                        wrapperStyle={{ paddingTop: '20px' }}
                                        formatter={() => 'Doanh thu (VNĐ)'}
                                    />
                                    <Bar
                                        dataKey="revenue"
                                        fill="#6366f1"
                                        radius={[8, 8, 0, 0]}
                                        name="Doanh thu"
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}