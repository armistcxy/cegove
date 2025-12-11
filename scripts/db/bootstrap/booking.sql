INSERT INTO showtimes (id, movie_id, screen_id, start_time, end_time, base_price, status) VALUES
('st_001', 'mv_101', 'sc_201', '2025-12-01 10:00:00+07', '2025-12-01 12:30:00+07', 80000.00, 0),
('st_002', 'mv_102', 'sc_202', '2025-12-01 14:00:00+07', '2025-12-01 16:15:00+07', 95000.00, 0),
('st_003', 'mv_101', 'sc_201', '2025-12-01 13:00:00+07', '2025-12-01 15:30:00+07', 80000.00, 0),
('st_004', 'mv_103', 'sc_203', '2025-12-02 18:30:00+07', '2025-12-02 21:00:00+07', 100000.00, 0),
('st_005', 'mv_102', 'sc_202', '2025-12-02 20:00:00+07', '2025-12-02 22:15:00+07', 95000.00, 0),
('st_006', 'mv_103', 'sc_203', '2025-12-03 11:30:00+07', '2025-12-03 14:00:00+07', 75000.00, 0),
('st_007', 'mv_104', 'sc_204', '2025-12-03 16:45:00+07', '2025-12-03 19:00:00+07', 85000.00, 0);

-- Cancelled showtime
INSERT INTO showtimes (id, movie_id, screen_id, start_time, end_time, base_price, status) VALUES
('st_008', 'mv_104', 'sc_204', '2025-12-03 20:00:00+07', '2025-12-03 22:15:00+07', 85000.00, 1);


CREATE OR REPLACE FUNCTION generate_seat_ids(rows INT, cols INT)
RETURNS TABLE(seat_id VARCHAR) AS $$
DECLARE
    r INT;
    c INT;
    row_char CHAR;
BEGIN
    FOR r IN 1..rows LOOP
        -- Chuyển số thành ký tự (1->A, 2->B, ...)
        row_char := chr(64 + r); 
        FOR c IN 1..cols LOOP
            seat_id := row_char || c;
            RETURN NEXT;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    v_showtime_id VARCHAR(255);
    v_base_price NUMERIC(10,2);
    v_seat_id VARCHAR(255);
    v_status SMALLINT;
    v_num_rows INT := 5; -- Số hàng ghế giả định
    v_num_cols INT := 8; -- Số cột ghế giả định
BEGIN
    -- Lặp qua TẤT CẢ các suất chiếu hiện có
    FOR v_showtime_id, v_base_price IN 
        SELECT id, base_price FROM showtimes
    LOOP
        -- Lặp qua TẤT CẢ các ghế được tạo giả định (A1 -> E8)
        FOR v_seat_id IN 
            SELECT * FROM generate_seat_ids(v_num_rows, v_num_cols)
        LOOP
            -- Thiết lập trạng thái: Ngẫu nhiên 10% ghế là đã đặt (status=1)
            IF random() < 0.1 THEN 
                v_status := 1; 
            ELSE
                v_status := 0; 
            END IF;

            -- Tính giá: Giá cơ bản + Phụ phí 10% cho ghế hàng A (Premium)
            IF v_seat_id LIKE 'A%' THEN
                INSERT INTO showtime_seats (seat_id, showtime_id, status, price, booking_id)
                VALUES (v_seat_id, v_showtime_id, v_status, v_base_price * 1.10, NULL);
            ELSE
                INSERT INTO showtime_seats (seat_id, showtime_id, status, price, booking_id)
                VALUES (v_seat_id, v_showtime_id, v_status, v_base_price, NULL);
            END IF;
        END LOOP;
    END LOOP;
    
    -- Cập nhật booking_id cho các ghế đã đặt (STATUS = 1)
    UPDATE showtime_seats
    SET booking_id = 'bkg_' || LPAD(CAST(FLOOR(random() * 9999 + 1) AS TEXT), 4, '0')
    WHERE status = 1 AND booking_id IS NULL;

END;
$$ LANGUAGE plpgsql;

-- Xóa hàm tạo ghế tạm thời sau khi sử dụng
DROP FUNCTION generate_seat_ids(rows INT, cols INT);