# cegove
Hệ thống đặt vé xem phim gồm các service quản lý các subdomain và tương tác với nhau để thực hiện nghiệp vụ cho hệ thống: 
- User Service: quản lý người dùng + authentication
- Cinema Service: quản lý cụm rạp, phòng chiếu, ghế ngồi
- Movie Service: quản lý thông tin phim
- Booking Service: xử lý quy trình đặt vé
- Payment Service: xử lý thanh toán
- Notification Service: thông báo cho người dùng
- Admin Service
- Recommendation Service: gợi ý phim cho người dùng dựa trên hành vi



## User Service
- Đăng ký, đăng nhập, xác thực
- Lưu lịch sử đặt vé
- Cấp quyền (role-based access)


## Cinema Service
- Lưu thông tin chi tiết về rạp
- Sơ đồ ghế (seat map)


## Movie Service
- CRUD phim, diễn viên, trailer, thể loại
- Cung cấp API cho frontend hiển thị danh sách phim

## Booking Service
- Nhận yêu cầu đặt vé (chọn suất chiếu, ghế, thanh toán…)
- Giữ ghế tạm thời (seat locking)
- Gửi yêu cầu đến Payment Service
- Xác nhận vé sau khi thanh toán thành công

## Payment Service
- Kết nối với cổng thanh toán (VNPay, MoMo, Stripe…)
- Giao tiếp với Booking Service để xác nhận thanh toán
- Ghi log giao dịch

## Notification Service
- Gửi email/xác nhận SMS sau khi đặt vé
- Nhắc lịch chiếu sắp tới

## Recommendation Service
- Gợi ý phim tương tự hoặc phổ biến
- Dựa trên lịch sử xem và đánh giá của user

## Admin Service
- Quản lý dữ liệu