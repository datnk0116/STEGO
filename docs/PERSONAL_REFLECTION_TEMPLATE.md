# Mẫu phản tư cá nhân — phải hoàn thiện trước khi nộp

Đây là bộ câu hỏi gợi ý, không phải bằng chứng cho đến khi sinh viên tự viết bằng trải nghiệm của mình.

## Phản tư (3–5 đoạn)

1. **Điểm xuất phát:** Trước đồ án, bạn đã biết gì về steganography ảnh/âm thanh, FFT/STFT, signal alignment hoặc CTF?
2. **Một giả thuyết thay đổi:** Nêu một giả định ban đầu cụ thể, output đã bác bỏ giả định đó và thay đổi bạn thực hiện trong code.
3. **Tự học:** Nêu khái niệm, API, thuật toán hoặc công cụ bạn tự tìm hiểu; ghi tài liệu gốc đã đọc và cách kiểm tra việc hiểu đúng.
4. **Đánh giá phản biện:** Kết quả nào có phạm vi hẹp hơn vẻ bề ngoài? Ví dụ: Sleepy Alarm sử dụng track gốc; audio robustness biến đổi target/reference theo cặp; Blue 3 đánh giá một decoder cụ thể.
5. **Hướng tiếp theo:** Nêu một thí nghiệm có thể thực hiện, biến độc lập, kết quả đo và giới hạn dự kiến.

## Nhật ký thời gian

Điền results/logbook-template.csv bằng giờ bắt đầu/kết thúc và thời lượng từ ghi chú thực tế, shell history hoặc lịch cá nhân. Nếu không xác định được giờ chính xác, để trống và giải thích; không tự dựng một tổng số giờ.

## Thông tin nộp bài

Điền họ tên đầy đủ, MSSV, lớp, ngày nộp và hạn nộp vào trang bìa và metadata PDF. Các trường này chủ động để trống trong mẫu.

## Các mốc kỹ thuật đã chuẩn bị từ repository

Các mốc dưới đây có thể được kiểm tra trong source/commit/log và chỉ là dữ kiện kỹ thuật để người thực hiện đối chiếu, không phải lời tự thuật:
- Blue 3: `results/logs/blue3-solver.log`, `results/blue3/analysis.json`.
- Sleepy Alarm lần chạy đầu thất bại: `results/2026-11-14/initial-run.md`.
- Sleepy Alarm exact-match: `results/sleepy_alarm/solver.json`.
- Robustness: CSV/JSON dưới `results/blue3/` và `results/sleepy_alarm/`.
- Unit/quality gate: log lịch sử và provenance ở `results/logs/` và `results/verification/`.

Người thực hiện phải tự xác nhận kiến thức trước khi làm, kiến thức mới thực sự tiếp thu, quyết định/sai lầm của bản thân, thời lượng từng phiên và hướng học tiếp. Nếu chưa xác nhận, để trống; không suy ra trải nghiệm từ commit/log.
