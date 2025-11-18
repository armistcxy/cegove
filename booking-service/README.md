## Functional Requirements
1. Quản lý lịch chiếu
2. Truy xuất và hiển thị trạng thái ghế ngồi
3. Giữ chỗ tạm thời (khi người dùng chọn một hoặc nhiều ghế thì phải khoá lại các ghế đó trong vòng 10 phút để họ thực hiện thanh toán)
4. Tạo đơn đặt vé và xác nhận đơn đặt vé
5. Tạo vé điện tử ở dạng QR và gọi đến Notification Service để gửi vé này cho người dùng qua email hoặc thông báo trên ứng dụng
6. Quản lý và truy xuất lịch sử đặt vé: Cung cấp API cho phép người dùng xem lại lịch sử các giao dịch đã thực hiện (bao gồm đã sử dụng và cả chưa sử dụng)

## Non-functional requirements
1. Consistency: Một ghế không thể được bán cho 2 người dùng khác nhau trong cùng một lúc
2. High performance: ervice phải xử lý được lưu lượng truy cập cực lớn, đặc biệt là khi mở bán vé cho một bộ phim "bom tấn". Thời gian phản hồi cho các thao tác như tải sơ đồ ghế hay giữ chỗ phải gần như tức thì
3. Scalability: Cần thiết kế để dễ scale hệ thống khi gặp trường hợp tải cao bất thường
4. Resilience: Booking Service giao tiếp với nhiều service nhất nên nó phải được thiết kế để xử lý trường hợp khi một trong các service gặp sự cố hoặc phản hồi chậm


## Domain

### Booking service

Mô hình domain của Booking Service với 4 thành phần chính quản lý việc đặt vé

**Seat** (Ghế ngồi)

- Đại diện cho một chiếc ghế vật lý trong một phòng chiếu cụ thể
- Trách nhiệm: Lưu trữ thông tin tĩnh và không thay đổi của một ghế, bao gồm vị trí (hàng, số) và loại ghế (Thường, VIP, Đôi)

**ShowtimeSeat** (Trạng thái ghế theo suất chiếu)

- Đại diện cho trạng thái “động” của một `Seat` tại một suất chiếu nhất định
- Trách nhiệm: Quản lý trạng thái của ghế (còn trống, đang được giữ, đã bán). Đây là đối tượng trung tâm của logic nghiệp vụ, được cập nhật liên tục trong quá trình người dùng chọn ghế và thanh toán.

**Booking (**Đơn đặt vé)

- Đại diện cho một giao dịch tài chính hoàn chỉnh của người dùng để mua một hoặc nhiều vé. Có thể ví Booking như một hóa đơn.
- Trách nhiệm: Cho phép gom nhóm nhiều `ShowtimeSeat` vào một lần mua. Theo dõi vòng đời giao dịch (chờ thanh toán, thành công, bị huỷ).

**Ticket** (Vé)

- Đại diện cho quyền vào cửa của một người tại một ghế ngồi cụ thể. Có thể coi `Ticket` là một món hàng trong `Booking`
- Ticket được tạo ra sau khi một Booking được xác nhận thanh toán thành công
- Trách nhiệm: Chứa tất cả thông tin cần thiết để được xác thực tại của soát vé (tên phim, rạp chiếu, giờ chiếu, vị trí, ghế, mã qr). Quản lý vòng đời sử dụng với các trạng thái hợp lệ, đã dùng, bị huỷ.