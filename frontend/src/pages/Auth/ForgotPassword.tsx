import { useState, useEffect } from "react";
import {resetPassword, sendOtp, verifyOtp} from "./Utils/ApiFunction.ts";
import {useNavigate} from "react-router-dom";

const ForgotPassword = () => {
    const navigate = useNavigate();

    const [step, setStep] = useState<1 | 2>(1);
    const [email, setEmail] = useState("");
    const [verificationCode, setVerificationCode] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [countdown, setCountdown] = useState(0);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    // Countdown timer
    useEffect(() => {
        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [countdown]);

    // Format countdown to MM:SS
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Handle send verification code
    const handleSendCode = async () => {
        if (!email) {
            setError("Vui lòng nhập email");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await sendOtp({
                email: email,
                otp: ''
            });

            await new Promise(resolve => setTimeout(resolve, 1000));

            if (response.status === 200) {
                setSuccess("Mã xác thực đã được gửi đến email của bạn");
                setCountdown(120);

                setTimeout(() => setSuccess(""), 3000);
            }
        } catch (err) {
            setError("Không thể gửi mã xác thực. Vui lòng thử lại.");
        } finally {
            setLoading(false);
        }
    };

    // Handle verify code
    const handleVerifyCode = async () => {
        if (!verificationCode) {
            setError("Vui lòng nhập mã xác thực");
            return;
        }

        if (verificationCode.length !== 6) {
            setError("Mã xác thực phải có 6 chữ số");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await verifyOtp({
                email: email,
                otp: verificationCode
            });

            await new Promise(resolve => setTimeout(resolve, 1000));

            if (response.status === 200 && response.data === true) {
                setStep(2);
                setSuccess("Xác thực thành công!");
                setTimeout(() => setSuccess(""), 3000);
            } else {
                setError("Mã xác thực không đúng");
            }
        } catch (err) {
            setError("Mã xác thực không đúng");
        } finally {
            setLoading(false);
        }
    };

    // Handle reset password
    const handleResetPassword = async () => {
        if (!newPassword || !confirmPassword) {
            setError("Vui lòng nhập đầy đủ thông tin");
            return;
        }

        if (newPassword.length < 6) {
            setError("Mật khẩu phải có ít nhất 6 ký tự");
            return;
        }

        if (newPassword !== confirmPassword) {
            setError("Mật khẩu xác nhận không khớp");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await resetPassword({
                email: email,
                otp: verificationCode,
                newPassword: newPassword,
                confirmNewPassword: confirmPassword
            });

            await new Promise(resolve => setTimeout(resolve, 1000));

            if (response.status === 200) {
                setSuccess("Đổi mật khẩu thành công! Đang chuyển về trang đăng nhập...");

                setTimeout(() => {
                    navigate("/login");
                }, 2000);
            }
        } catch (err) {
            setError("Không thể đổi mật khẩu. Vui lòng thử lại.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
                <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
                    Quên mật khẩu
                </h1>
                <p className="text-center text-gray-600 mb-8">
                    {step === 1 ? "Nhập email để nhận mã xác thực" : "Tạo mật khẩu mới"}
                </p>

                {/* Step indicator */}
                <div className="flex items-center justify-center mb-8">
                    <div className="flex items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                            step >= 1 ? "bg-red-600 text-white" : "bg-gray-200 text-gray-600"
                        }`}>
                            1
                        </div>
                        <div className={`w-20 h-1 ${step >= 2 ? "bg-red-600" : "bg-gray-200"}`}></div>
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                            step >= 2 ? "bg-red-600 text-white" : "bg-gray-200 text-gray-600"
                        }`}>
                            2
                        </div>
                    </div>
                </div>

                {/* Success Message */}
                {success && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm mb-5">
                        {success}
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-5">
                        {error}
                    </div>
                )}

                {step === 1 ? (
                    // Step 1: Email and Verification Code
                    <div>
                        <div className="mb-5">
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                Email
                            </label>
                            <input
                                type="email"
                                id="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="example@gmail.com"
                                className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                                disabled={countdown > 0}
                            />
                        </div>

                        <div className="mb-5">
                            <button
                                onClick={handleSendCode}
                                disabled={loading || countdown > 0}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {countdown > 0
                                    ? `Gửi lại sau ${formatTime(countdown)}`
                                    : loading
                                        ? "Đang gửi..."
                                        : "Gửi mã xác thực"
                                }
                            </button>
                        </div>

                        <div className="mb-5">
                            <label className="block text-sm font-medium text-gray-700 mb-2 text-center">
                                Mã xác thực (6 chữ số)
                            </label>
                            <div className="flex gap-2 justify-center">
                                {[0, 1, 2, 3, 4, 5].map((index) => (
                                    <input
                                        key={index}
                                        id={`code-${index}`}
                                        type="text"
                                        maxLength={1}
                                        value={verificationCode[index] || ''}
                                        onChange={(e) => {
                                            const value = e.target.value.replace(/\D/g, '');
                                            if (value) {
                                                const newCode = verificationCode.split('');
                                                newCode[index] = value;
                                                setVerificationCode(newCode.join(''));

                                                // Auto focus next input
                                                if (index < 5) {
                                                    document.getElementById(`code-${index + 1}`)?.focus();
                                                }
                                            }
                                        }}
                                        onKeyDown={(e) => {
                                            // Handle backspace
                                            if (e.key === 'Backspace' && !verificationCode[index] && index > 0) {
                                                document.getElementById(`code-${index - 1}`)?.focus();
                                            }
                                        }}
                                        onPaste={(e) => {
                                            e.preventDefault();
                                            const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
                                            setVerificationCode(pastedData);

                                            // Focus last filled input or last input
                                            const nextIndex = Math.min(pastedData.length, 5);
                                            document.getElementById(`code-${nextIndex}`)?.focus();
                                        }}
                                        className="w-12 h-14 text-center text-2xl font-bold bg-gray-50 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                                    />
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={handleVerifyCode}
                            disabled={loading || verificationCode.length !== 6}
                            className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Đang xác thực..." : "Xác thực"}
                        </button>

                        <div className="text-center mt-6">
                            <a href="/login" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
                                Quay lại đăng nhập
                            </a>
                        </div>
                    </div>
                ) : (
                    // Step 2: New Password
                    <div>
                        <div className="mb-5">
                            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                Mật khẩu mới
                            </label>
                            <input
                                type="password"
                                id="newPassword"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="••••••••••••"
                                className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                            />
                        </div>

                        <div className="mb-5">
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                Xác nhận mật khẩu mới
                            </label>
                            <input
                                type="password"
                                id="confirmPassword"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••••••"
                                className="w-full px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                            />
                        </div>

                        <button
                            onClick={handleResetPassword}
                            disabled={loading}
                            className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Đang đổi mật khẩu..." : "Đổi mật khẩu"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ForgotPassword;