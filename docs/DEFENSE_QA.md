# Hướng dẫn tự bảo vệ đồ án — UET.CN3124 Steganography

Tài liệu này dùng để ôn tập và diễn giải code của chính repository. Không học thuộc câu trả lời; hãy mở đúng file, chạy lệnh và giải thích bằng lời của mình.

## 1. Vì sao chọn hai challenge?

Cả hai cùng thuộc steganography nhưng nằm ở hai miền vật mang tin khác nhau:
- Blue 3: ẩn dữ liệu trên miền không gian của ảnh, giải bằng tổng sai khác RGB theo các vùng vuông chéo.
- Sleepy Alarm: ẩn dữ liệu trên miền tín hiệu âm thanh bằng ASK, cần căn chỉnh audio, chọn channel, phát hiện symbol và giải mã byte.

Đây là một nghiên cứu so sánh hai cơ chế, không phải tuyên bố rằng hai mẫu đại diện cho mọi kỹ thuật steganography.

## 2. Blue 3 — câu hỏi cần trả lời được

**Tại sao tổng sai khác RGB khôi phục được ký tự?**

Creator bắt đầu từ màu nền đồng nhất và tăng đúng một đơn vị ở đúng một kênh cho mỗi đơn vị mã ký tự. Tổng sai khác trong vùng là phép cộng: mỗi lần tăng đóng góp một đơn vị, bất kể pixel hay kênh nào được chọn. Vì vậy tổng bằng code point khi màu nền, độ dài vùng và kích thước ảnh được xác định đúng và ảnh chưa bị biến đổi.

**Vì sao suy luận màu nền bằng modal RGB?**

Màu nền chiếm phần lớn ảnh gốc, nên bộ RGB xuất hiện nhiều nhất có thể ước lượng màu nền. Đây là giả định đặc thù challenge; nó có thể sai nếu cover có texture, payload sửa quá nhiều pixel hoặc ảnh đã qua xử lý.

**Vì sao JPEG/resize làm decoder thất bại?**

JPEG thay đổi giá trị pixel qua nén mất dữ liệu; resize nội suy pixel và thay đổi ranh giới, số pixel trong các vùng. Thí nghiệm chỉ chứng minh decoder này không khôi phục được chuỗi ở các mức thử nghiệm, không chứng minh payload bị xóa hoàn toàn hoặc mọi kỹ thuật ảnh đều thất bại.

## 3. Sleepy Alarm — câu hỏi cần trả lời được

**Mô hình tín hiệu là gì?**

Creator dùng sóng mang 8 kHz, tốc độ 50 baud và 0,02 giây mỗi symbol. Với sample rate 44,1 kHz, một symbol gồm 882 mẫu và 160 chu kỳ sóng mang. Ba mức biên độ biểu diễn separator, bit 0 và bit 1.

**Vì sao cần căn chỉnh reference?**

Hai file MP3 có độ trễ mã hóa và số frame khác nhau. Cross-correlation ước lượng độ lệch; chỉ phần overlap mới có thể trừ trực tiếp. Cần giữ các mẫu đầu của distributed track bị loại khỏi overlap vì chúng có thể chứa bit đầu tiên.

**Vì sao chỉ phân tích kênh trái?**

Creator MATLAB cộng ASK vào channel thứ nhất. Lấy trung bình hai kênh làm suy giảm tín hiệu được nhúng và thay đổi các mức biên độ.

**Vì sao dùng coherent I/Q projection?**

Mỗi symbol 882 mẫu chứa đúng 160 chu kỳ sóng mang. Chiếu symbol lên hai cơ sở sin/cos tại tần số carrier để thu I và Q, sau đó lấy độ lớn vector I/Q để ước lượng biên độ. Cách này tận dụng toàn bộ symbol và tránh transient của bộ lọc/Hilbert ở ranh giới.

**Correlation 0,999873 có chứng minh flag đúng không?**

Không. Correlation đo mức tương đồng/căn chỉnh của hai track, không đo độ đúng của bộ phân loại symbol. Lần chạy đầu có correlation cao nhưng trả về byte NUL vì phân tích sai kênh và sai khoảng thời gian. Điều kiện xác minh cuối là exact-match toàn bộ chuỗi với ground truth độc lập trích từ creator bitmap.

**Giải pháp có hoàn toàn black-box không?**

Không. Decoder dùng track gốc để loại nền và tham khảo mô tả creator. Đây là lợi thế reference-assisted/white-box cần được ghi rõ. Decoder không có reference là hướng nghiên cứu tiếp theo.

## 4. Giới hạn của thí nghiệm robustness

Các phép JPEG/resize chỉ đánh giá một decoder Blue 3 với những tham số đã liệt kê. Các phép audio được áp dụng đồng thời cho target và reference; kết quả không chứng minh khả năng chịu được biến đổi bất đối xứng khi chỉ một file bị sửa. Không khái quát các kết quả này cho codec hoặc phương pháp steganography khác.

## 5. Thí nghiệm bổ sung: robustness bất đối xứng

Bản robustness ban đầu áp dụng phép biến đổi đồng thời lên target và reference. Để tránh đánh đồng kết quả này với khả năng chịu biến đổi một phía, repository có thêm script riêng:

~~~bash
python src/experiments/sleepy_alarm_asymmetric_robustness.py \\
  data/sleepy_alarm/morning_n_breakfast.mp3 \\
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \\
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
~~~

Script kiểm tra target-only/reference-only với gain và resampling round-trip. Chỉ diễn giải các kết quả thực tế trong JSON/CSV sau khi chạy; không giả định trước trường hợp nào phải PASS hay FAIL.

## 6. Bằng chứng cần mở khi vấn đáp

- Manifest và SHA-256 của ba artifact.
- Log của sáu regression tests.
- Blue 3 solver log và hình diagnostics.
- Sleepy Alarm solver JSON: số symbol, tâm cụm, byte lỗi, exact-match.
- Hai file CSV robustness.
- Lệnh build DOCX/PDF/ZIP tại máy, không cần GitHub Actions.

Lệnh kiểm chứng:

~~~bash
python -m unittest discover -s tests -v
python src/solve_challenges.py blue3 data/blue3/blue.png
python src/solve_challenges.py sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
python scripts/build_submission.py
~~~

## 7. Phản tư cá nhân — tự viết bằng trải nghiệm thật

Trước buổi bảo vệ, hãy chuẩn bị câu trả lời cụ thể:
1. Ban đầu bạn tin giả thuyết nào, và dữ liệu nào khiến bạn thay đổi?
2. Bạn tự học thêm khái niệm, API, thuật toán hoặc công cụ nào? Nguồn tài liệu nào giúp bạn hiểu?
3. Lần thất bại nào mang lại thông tin hữu ích nhất, và vì sao?
4. Phần nào trong decoder bạn có thể viết lại từ đầu mà không nhìn source?
5. Bạn sẽ thiết kế thí nghiệm tiếp theo nào, biến độc lập là gì và đo thành công bằng chỉ số nào?

Không khai khống thời gian, screenshot, thao tác hoặc hoạt động chưa thực hiện.
