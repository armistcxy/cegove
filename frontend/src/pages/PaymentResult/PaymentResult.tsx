import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

function parseQuery(queryString: string) {
    const params = new URLSearchParams(queryString);
    const result: Record<string, string> = {};
    params.forEach((value, key) => {
        result[key] = value;
    });
    return result;
}

const statusMap: Record<string, { text: string; className: string; icon: string }> = {
    "00": { text: "Thanh toán thành công", className: "success", icon: "✅" },
    "24": { text: "Đã hủy bởi khách hàng", className: "failed", icon: "❌" },
    "07": { text: "Giao dịch bị nghi ngờ", className: "failed", icon: "❌" },
    "09": { text: "Giao dịch chưa hoàn tất", className: "failed", icon: "❌" },
    "10": { text: "Giao dịch không thành công do sai thông tin", className: "failed", icon: "❌" },
    "11": { text: "Đã hết hạn chờ thanh toán", className: "failed", icon: "❌" },
    "12": { text: "Thẻ bị khóa", className: "failed", icon: "❌" },
    "13": { text: "Sai mật khẩu xác thực giao dịch", className: "failed", icon: "❌" },
    "51": { text: "Tài khoản không đủ số dư", className: "failed", icon: "❌" },
    "65": { text: "Tài khoản đã vượt quá hạn mức giao dịch", className: "failed", icon: "❌" },
    "default": { text: "Giao dịch thất bại", className: "failed", icon: "❌" },
};

const PaymentResult: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const params = parseQuery(location.search);
    const responseCode = params["vnp_ResponseCode"];
    const status = statusMap[responseCode] || statusMap["default"];

    // Format amount (VNPay returns amount * 100)
    const formatAmount = (amountStr: string) => {
        if (!amountStr) return "N/A";
        const amount = parseInt(amountStr) / 100;
        return amount.toLocaleString('vi-VN') + " VND";
    };

    // Format date from VNPay format (YYYYMMDDHHmmss)
    const formatDate = (dateStr: string) => {
        if (!dateStr || dateStr.length !== 14) return dateStr;
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        const hour = dateStr.substring(8, 10);
        const minute = dateStr.substring(10, 12);
        const second = dateStr.substring(12, 14);
        return `${day}/${month}/${year} ${hour}:${minute}:${second}`;
    };

    // Display fields in a specific order with better labels
    const displayFields = [
        { label: "Mã giao dịch", key: "vnp_TxnRef" },
        { label: "Mã phản hồi", key: "vnp_ResponseCode" },
        { label: "Số tiền", key: "vnp_Amount", format: "amount" },
        { label: "Ngân hàng", key: "vnp_BankCode" },
        { label: "Loại thẻ", key: "vnp_CardType" },
        { label: "Mã TMN", key: "vnp_TmnCode" },
        { label: "Thời gian thanh toán", key: "vnp_PayDate", format: "date" },
        { label: "Số giao dịch", key: "vnp_TransactionNo" },
        { label: "Trạng thái giao dịch", key: "vnp_TransactionStatus" },
        { label: "Thông tin đơn hàng", key: "vnp_OrderInfo" },
    ];

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 py-8">
            <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full">
                <h1 className="text-2xl font-bold mb-2">💳 Kết quả thanh toán</h1>
                <p className="text-gray-600 mb-6">Chi tiết giao dịch VNPay</p>

                <div className={`inline-block px-4 py-2 rounded-full font-semibold mb-6 ${
                    status.className === "success"
                        ? "bg-green-100 text-green-700 border border-green-300"
                        : "bg-red-100 text-red-700 border border-red-300"
                }`}>
                    {status.icon} {status.text}
                </div>

                <div className="mb-8 border border-gray-200 rounded-lg p-4">
                    {displayFields.map((field) => {
                        const value = params[field.key];
                        if (!value) return null;

                        let displayValue = value;
                        if (field.format === "amount") {
                            displayValue = formatAmount(value);
                        } else if (field.format === "date") {
                            displayValue = formatDate(value);
                        }

                        return (
                            <div key={field.key} className="flex justify-between py-3 border-b border-gray-100 last:border-b-0">
                                <div className="font-semibold text-gray-700 w-1/3">{field.label}</div>
                                <div className="text-gray-900 break-all font-mono text-sm w-2/3 text-right">
                                    {displayValue}
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="flex gap-4">
                    <button
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-bold transition"
                        onClick={() => navigate("/")}
                    >
                        Về trang chủ
                    </button>
                    <button
                        className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-3 rounded-lg font-bold transition"
                        onClick={() => navigate("/my-tickets")}
                    >
                        Xem vé của tôi
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PaymentResult;
