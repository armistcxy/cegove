import React, {useEffect, useState} from "react";
import {Link, useNavigate} from "react-router-dom";
import type {LoginForm, RegistrationForm} from "./Utils/Type.ts";
import {login, register} from "./Utils/ApiFunction.ts";
import provinceData from "../../assets/province_data.json"
import { useUser } from "../../context/UserContext.tsx";

const AuthPage = () => {
    const navigate = useNavigate();
    const { refreshUserProfile } = useUser();

    const [loginForm, setLoginForm] = useState<LoginForm>({
        username: "",
        password: "",
    });

    const [registerForm, setRegisterForm] = useState<RegistrationForm>({
        fullName: "",
        email: "",
        phone: "",
        password: "",
        dob: "",
        address: "",
        district: "",
        city: "",
        gender: "MALE",
        img: null,
    });

    const cities = Object.keys(provinceData);
    const districts = registerForm.city ? provinceData[registerForm.city] : [];

    const activeTab = location.pathname === "/login" ? "login" : "register";

    const [error, setError] = useState("");
    const [registerSuccess, setRegisterSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const urlError = params.get('error');
        if (urlError && urlError !== error) {
            setError(urlError);
            setTimeout(() => {
                setError("");
                navigate("/login");
            }, 3000)
        }
    }, [error, navigate]);

    const handleChangeTab = (tab: "login" | "register") => {
        navigate(`/${tab}`);
    }

    const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setLoginForm(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setRegisterForm(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const setSelectedGender = (gender) => {
        setRegisterForm(prev => ({
            ...prev,
            gender: gender,
        }));
    }

    const setSelectedCity = (city: string) => {
        setRegisterForm(prev => ({
            ...prev,
            city: city,
            district: "", // reset district when city changes
        }));
    }

    const setSelectedDistrict = (district: string) => {
        setRegisterForm(prev => ({
            ...prev,
            district: district,
        }));
    }

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        setLoading(true);
        try {
            const response = await login(loginForm);
            if (response.status === 200) {
                const token = response.data;
                localStorage.setItem("access-token", token);

                await refreshUserProfile();
                navigate("/");
            }
        } catch (error) {
            if (error.response && error.response.status === 401) {
                setError("Mật khẩu không đúng. Vui lòng thử lại.");
            } else if (error.response && error.response.status === 403) {
                setError("Tài khoản của bạn được đăng nhập qua Google. Vui lòng sử dụng đăng nhập Google.");
            } else if (error.response && error.response.status === 404) {
                setError("Tài khoản không tồn tại. Vui lòng đăng ký trước.");
            } else {
                setError("An error occurred. Please try again later.");
            }

            setTimeout(() => {
                setError("");
            }, 3000);

        }
        setLoading(false);
    }

    const handleRegisterSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await register(registerForm);
            if (response.status === 200) {
                setRegisterSuccess(true);
                setTimeout(() => {
                    navigate("/login");
                }, 1500);
            }
        } catch (error) {
            if (error.response && error.response.status === 409) {
                setError("Email hoặc số điện thoại đã được sử dụng. Vui lòng thử lại.");
            } else {
                setError("Có lỗi xảy ra. Vui lòng thử lại sau.");
            }

            setRegisterSuccess(false);
            setTimeout(() => {
                setError("");
            }, 3000);

        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-white rounded-lg shadow-lg overflow-hidden">
                {/* Tabs Header */}
                <div className="flex">
                    <button
                        onClick={() => handleChangeTab("login")}
                        className={`flex-1 py-4 font-bold text-base transition-colors ${
                            activeTab === "login"
                                ? "bg-red-600 text-white"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                    >
                        ĐĂNG NHẬP
                    </button>
                    <button
                        onClick={() => handleChangeTab("register")}
                        className={`flex-1 py-4 font-bold text-base transition-colors ${
                            activeTab === "register"
                                ? "bg-red-600 text-white"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                    >
                        ĐĂNG KÝ
                    </button>
                </div>

                {/* Form Content */}
                <div className="p-8">
                    {activeTab === "login" ? (
                        // Login Form
                        <div>
                            <div className="mb-5">
                                <label htmlFor="login-username" className="block text-sm font-medium text-gray-700 mb-2">
                                    Email hoặc Số điện thoại
                                </label>
                                <input
                                    type="text"
                                    id="login-username"
                                    name="username"
                                    value={loginForm.username}
                                    onChange={handleLoginChange}
                                    placeholder="email@example.com hoặc 0123456789"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                />
                            </div>

                            <div className="mb-5">
                                <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-2">
                                    Mật khẩu
                                </label>
                                <input
                                    type="password"
                                    id="login-password"
                                    name="password"
                                    value={loginForm.password}
                                    onChange={handleLoginChange}
                                    placeholder="••••••••••••"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                />
                            </div>

                            {error && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-5">
                                    {error}
                                </div>
                            )}

                            <div className="mb-4">
                                <button
                                    onClick={handleLoginSubmit}
                                    disabled={loading}
                                    className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-base"
                                >
                                    {loading ? "ĐANG ĐĂNG NHẬP..." : "ĐĂNG NHẬP"}
                                </button>
                            </div>

                            <div className="text-center mb-6">
                                <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
                                    Bạn muốn tìm lại mật khẩu?
                                </Link>
                            </div>

                            <div className="relative mb-6">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-gray-200"></div>
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-2 bg-white text-gray-500">hoặc</span>
                                </div>
                            </div>

                            <div className="flex items-center justify-center">
                                <a
                                    href="https://auth.cegove.cloud/oauth2/authorization/google"
                                    className="flex items-center gap-3 bg-white border border-gray-300 hover:border-gray-400 px-6 py-2.5 rounded-lg transition duration-200 shadow-sm hover:shadow"
                                >
                                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                                        <path
                                            fill="#4285F4"
                                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                        />
                                        <path
                                            fill="#34A853"
                                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                        />
                                        <path
                                            fill="#FBBC05"
                                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                        />
                                        <path
                                            fill="#EA4335"
                                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                        />
                                    </svg>
                                    <span className="text-gray-700 font-medium">Login with Google</span>
                                </a>
                            </div>
                        </div>
                    ) : (
                        // Register Form
                        <div>
                            <div className="mb-4">
                                <label htmlFor="register-fullName" className="block text-sm font-medium text-gray-700 mb-2">
                                    Họ và tên
                                </label>
                                <input
                                    type="text"
                                    id="register-fullName"
                                    name="fullName"
                                    value={registerForm.fullName}
                                    onChange={handleRegisterChange}
                                    placeholder="Nguyễn Văn A"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-email" className="block text-sm font-medium text-gray-700 mb-2">
                                    Email
                                </label>
                                <input
                                    type="email"
                                    id="register-email"
                                    name="email"
                                    value={registerForm.email}
                                    onChange={handleRegisterChange}
                                    placeholder="example@gmail.com"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-phone" className="block text-sm font-medium text-gray-700 mb-2">
                                    Số điện thoại
                                </label>
                                <input
                                    type="tel"
                                    id="register-phone"
                                    name="phone"
                                    value={registerForm.phone}
                                    onChange={handleRegisterChange}
                                    placeholder="0123456789"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-password" className="block text-sm font-medium text-gray-700 mb-2">
                                    Mật khẩu
                                </label>
                                <input
                                    type="password"
                                    id="register-password"
                                    name="password"
                                    value={registerForm.password}
                                    onChange={handleRegisterChange}
                                    placeholder="••••••••••••"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-dob" className="block text-sm font-medium text-gray-700 mb-2">
                                    Ngày sinh
                                </label>
                                <input
                                    type="date"
                                    id="register-dob"
                                    name="dob"
                                    value={registerForm.dob}
                                    onChange={handleRegisterChange}
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-gender" className="block text-sm font-medium text-gray-700 mb-2">
                                    Giới tính
                                </label>
                                <select
                                    id="register-gender"
                                    name="gender"
                                    value={registerForm.gender}
                                    onChange={(e) => setSelectedGender(e.target.value)}
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                >
                                    <option value="MALE">Nam</option>
                                    <option value="FEMALE">Nữ</option>
                                    <option value="OTHER">Khác</option>
                                </select>
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-city" className="block text-sm font-medium text-gray-700 mb-2">
                                    Thành phố
                                </label>
                                <select
                                    id="register-city"
                                    name="city"
                                    value={registerForm.city}
                                    onChange={(e) => setSelectedCity(e.target.value)}
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                >
                                    <option value="">Chọn tỉnh/thành phố</option>
                                    {cities.map((city) => (
                                        <option key={city} value={city}>
                                            {city}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-district" className="block text-sm font-medium text-gray-700 mb-2">
                                    Quận/Huyện
                                </label>
                                <select
                                    id="register-district"
                                    name="district"
                                    value={registerForm.district}
                                    onChange={(e) => setSelectedDistrict(e.target.value)}
                                    disabled={!registerForm.city}
                                    required
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                >
                                    <option value="">Chọn quận/huyện</option>
                                    {districts.map((district: string) => (
                                        <option key={district} value={district}>
                                            {district}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="mb-4">
                                <label htmlFor="register-address" className="block text-sm font-medium text-gray-700 mb-2">
                                    Địa chỉ
                                </label>
                                <input
                                    type="text"
                                    id="register-address"
                                    name="address"
                                    value={registerForm.address}
                                    onChange={handleRegisterChange}
                                    placeholder="123 Đường ABC"
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                    required
                                />
                            </div>

                            <div className="mb-5">
                                <label htmlFor="register-img" className="block text-sm font-medium text-gray-700 mb-2">
                                    Ảnh đại diện
                                </label>
                                <input
                                    type="file"
                                    id="register-img"
                                    name="img"
                                    accept="image/*"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0] || null;
                                        setRegisterForm(prev => ({
                                            ...prev,
                                            img: file,
                                        }));
                                    }}
                                    className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100"
                                />
                            </div>

                            {registerSuccess && (
                                <div className="bg-red-50 border border-red-200 text-green-500 px-4 py-3 rounded-lg text-sm mb-5">
                                    Đăng ký thành công! Chuyển đến trang đăng nhập...
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-5">
                                    {error}
                                </div>
                            )}

                            <div className="mb-4">
                                <button
                                    onClick={handleRegisterSubmit}
                                    disabled={loading}
                                    className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-base"
                                >
                                    {loading ? "ĐANG ĐĂNG KÝ..." : "ĐĂNG KÝ"}
                                </button>
                            </div>

                            {/*<div className="relative mb-6">*/}
                            {/*    <div className="absolute inset-0 flex items-center">*/}
                            {/*        <div className="w-full border-t border-gray-200"></div>*/}
                            {/*    </div>*/}
                            {/*    <div className="relative flex justify-center text-sm">*/}
                            {/*        <span className="px-2 bg-white text-gray-500">hoặc</span>*/}
                            {/*    </div>*/}
                            {/*</div>*/}

                            {/*<div className="flex items-center justify-center">*/}
                            {/*    <button*/}
                            {/*        type="button"*/}
                            {/*        className="flex items-center gap-3 bg-white border border-gray-300 hover:border-gray-400 px-6 py-2.5 rounded-lg transition duration-200 shadow-sm hover:shadow"*/}
                            {/*    >*/}
                            {/*        <svg className="w-5 h-5" viewBox="0 0 24 24">*/}
                            {/*            <path*/}
                            {/*                fill="#4285F4"*/}
                            {/*                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"*/}
                            {/*            />*/}
                            {/*            <path*/}
                            {/*                fill="#34A853"*/}
                            {/*                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"*/}
                            {/*            />*/}
                            {/*            <path*/}
                            {/*                fill="#FBBC05"*/}
                            {/*                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"*/}
                            {/*            />*/}
                            {/*            <path*/}
                            {/*                fill="#EA4335"*/}
                            {/*                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"*/}
                            {/*            />*/}
                            {/*        </svg>*/}
                            {/*        <span className="text-gray-700 font-medium">Sign up with Google</span>*/}
                            {/*    </button>*/}
                            {/*</div>*/}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AuthPage;