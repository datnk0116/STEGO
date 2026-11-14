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
python src/experiments/sleepy_alarm_asymmetric_robustness.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
~~~

Kết quả đã đo: baseline PASS; target-only gain 0,5× FAIL (46 separator), target-only gain 1,5× FAIL (37 separator), target-only resampling PASS (38 separator), reference-only gain 0,5× FAIL (41 separator), reference-only gain 1,5× FAIL (38 separator), reference-only resampling PASS (38 separator). Tổng cộng 3/6 phép thử PASS. Bốn phép gain một phía thất bại dù alignment correlation vẫn xấp xỉ 0,99888–0,99987; hai phép resampling một phía thành công. Điều này cho thấy correlation cao chỉ hỗ trợ đánh giá căn chỉnh, không bảo đảm phân loại đúng biên độ ASK. Xem JSON/CSV để kiểm tra decoded text, lỗi byte, clipping và runtime.

## 6. Bằng chứng cần mở khi vấn đáp

- Manifest và SHA-256 của ba artifact.
- Log unit-tests.log chỉ là lịch sử sáu regression tests; quality-gate-tests.log ghi 22/22 tests pass tại revision a040e38. Commit 3bb2b57 lưu các tệp bằng chứng, không đổi source/tests.
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


## 8. Đối chiếu với công cụ mã nguồn mở

**Aperi'Solve có gì khác STEGO?**
Aperi'Solve là nền tảng phân tích ảnh, trực quan hóa bit-plane và tích hợp nhiều công cụ như zsteg, steghide, outguess, exiftool, binwalk và foremost. STEGO không cạnh tranh về độ rộng detector; đồ án tập trung giải thích và tái hiện hai cơ chế challenge cụ thể. Blue 3 dùng tổng sai khác RGB theo vùng, không phải LSB.

**The-A-Files gợi ý điều gì cho đánh giá audio?**
Repository này tách payload recovery, signal quality, robustness, capacity và detectability, đồng thời mô tả nhiều phương pháp và phép attack. STEGO hiện mới có exact-match và một tập phép biến đổi nhỏ trên một challenge ASK. Muốn mở rộng cần thêm corpus, BER, metric chất lượng và nhiều mức cường độ attack.

**Có thể nói STEGO tốt hơn các repository trên không?**
Không. Chưa có benchmark trực tiếp trên cùng dữ liệu, cùng môi trường và cùng tiêu chí. Có thể kết luận STEGO có phạm vi hẹp nhưng có phân tích chi tiết hai challenge; không thể kết luận vượt trội về hiệu năng hoặc khả năng phát hiện tổng quát.

**Vì sao chưa dùng Aperi'Solve hoặc LSB tools để giải hai challenge?**
Các công cụ đó tập trung vào nhiều họ steganography phổ biến, đặc biệt bit-plane/LSB và metadata. Blue 3 dùng tổng sai khác RGB theo vùng; Sleepy Alarm dùng ASK 8 kHz và cần reference alignment. Chúng có thể là công cụ khảo sát bổ sung, nhưng không mặc nhiên là decoder tương thích với hai cơ chế này.


## 9. Detector baseline và đánh giá

**Detector hiện tại có chứng minh phát hiện được steganography tổng quát không?**

Không. `src/steganalysis.py` là baseline heuristic có thể giải thích: ảnh dùng tỷ lệ màu RGB phổ biến và độ lệch chuẩn kênh; audio dùng tỷ lệ năng lượng quanh 8 kHz và độ biến thiên RMS theo block 50 baud. Ngưỡng được đặt cố định, chưa được hiệu chuẩn trên corpus độc lập. Ảnh đơn sắc và audio có carrier tự nhiên có thể gây false positive.

**Precision, Recall, F1 và FPR hiện được tính trên dữ liệu nào?**

Benchmark tạo benign controls tổng hợp bằng seed 20261114, cùng các biến thể dẫn xuất từ hai artifact stego chính thức. Đây là bộ kiểm thử minh họa khả năng chạy pipeline, không đại diện dữ liệu đời thực; số lượng positive nhỏ và không được dùng để tuyên bố tổng quát hóa.

**Làm sao chạy thử giải mã audio không reference?**

Chạy `python src/solve_challenges.py sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3` và không truyền `--reference`. Bằng chứng hiện tại: 350 symbol, 49 separator, giải ra 26 ký tự và format không hợp lệ. Đây là thất bại có ý nghĩa trong threat model blind, không phải thành công; cần phương pháp đồng bộ/ước lượng nền không phụ thuộc track gốc.

**Thí nghiệm robustness mới bổ sung gì?**

Blue 3 có 9 biến thể exact-match 1/9 và metric partial recovery; ví dụ brightness 0,9 còn 47/50 ký tự đúng. Sleepy Alarm có 23 trial, 7 PASS; mean SER 12,31%, mean BER 12,97%, separator precision 77,07% và recall 93,14% (trung bình theo trial, tính baseline). Các phép biến đổi gồm gain, AWGN, band-pass và resampling áp dụng riêng cho target hoặc reference. Đây là một ma trận trên một artifact, không phải ước lượng thống kê quần thể.

## 10. Phản biện nâng cao: câu hỏi giảng viên có thể hỏi

**Threat model của đồ án là gì? Có giải được trong tình huống blind steganalysis không?**

Không hoàn toàn. Blue 3 được phân tích với hiểu biết về creator algorithm và giả định ảnh PNG gốc. Sleepy Alarm hiện là reference-assisted vì cần track gốc để tạo residual. Thử reference-free đã chạy nhưng thất bại: 350 symbol, 49 separator, 26 ký tự, format invalid. Vì vậy không tuyên bố đây là blind decoder.

**Vì sao Sleepy Alarm có correlation gần 1 nhưng vẫn sai khi gain một phía?**

Cross-correlation chuẩn hóa chủ yếu phản ánh tương đồng hình dạng/độ trễ, không đảm bảo scale của hai track bằng nhau. Khi chỉ target hoặc reference bị gain, phép trừ residual để lại thành phần nền không triệt tiêu đúng; ba cụm ASK có thể chồng lấn hoặc lệch. Dữ liệu cho thấy correlation khoảng 0,99888–0,99987 trong nhiều trường hợp gain FAIL. Cần xem cluster centers và byte errors để kết luận cụ thể cho từng trường hợp.

**Tại sao detector audio có recall bằng 0?**

Detector yêu cầu đồng thời carrier-band energy ratio >= 0,02 và block-RMS coefficient of variation >= 0,15. Positive audio trong benchmark có carrier ratio khoảng 0,000204, thấp hơn ngưỡng hơn hai bậc độ lớn; dù RMS CV cao khoảng 0,987, điều kiện AND vẫn làm detector bỏ qua tất cả positive. Không nên chỉ hạ threshold dựa trên cùng benchmark; phải dùng validation độc lập, giữ test set riêng.

**Ảnh detector có precision/recall/F1 = 1 có chứng minh detector tốt?**

Không. Năm positive đều là bản gốc/biến thể brightness cùng nguồn Blue 3, còn 12 negative là synthetic. Đây không phải mẫu ảnh độc lập đại diện cho ảnh tự nhiên. Kết quả xác nhận heuristic phân biệt nhóm mẫu đã tạo, không xác nhận generalization.

**Blue 3 thất bại sau JPEG/resize có chứng minh dữ liệu ẩn bị xóa?**

Không. Kết quả chỉ xác nhận decoder hiện tại không khôi phục được payload theo đúng phép tổng pixel và phân vùng cũ. Một phương pháp khác có thể còn khôi phục được một phần payload. Cần báo BER hoặc tỷ lệ ký tự phục hồi trước khi nói payload bị phá hủy.

**Thành công 4/4 audio paired robustness có mâu thuẫn với 3/6 asymmetric robustness không?**

Không. Thử nghiệm paired áp dụng cùng phép biến đổi lên target và reference, giữ scale tương đối. Thử nghiệm asymmetric chỉ biến đổi một phía; bốn gain một phía thất bại, hai resampling round-trip một phía thành công. Hai nhóm có điều kiện khác nhau nên phải báo riêng.

**Đóng góp mới của đồ án là gì nếu challenge source/writeup đã tồn tại?**

Đóng góp không phải phát minh thuật toán ẩn tin mới. Đóng góp trong phạm vi bài thực hành là tái triển khai decoder, phân tích điều kiện hoạt động, ghi lại lỗi trong quá trình debug, exact-match với ground truth độc lập, đo robustness và trình bày giới hạn định lượng. Cần phân biệt đóng góp học tập/kỹ thuật này với novelty nghiên cứu.

**Em sẽ ưu tiên cải tiến điều gì đầu tiên?**

Quality gate P0 đã hoàn tất: 22/22 tests pass, ba artifact đúng hash và hai decoder exact-match trong điều kiện đã nêu; log/JSON đã được commit. Ưu tiên kỹ thuật tiếp theo là (1) xây dựng corpus detector đa nguồn có validation/test độc lập, (2) nghiên cứu reference-free synchronization cho Sleepy Alarm, và (3) mở rộng robustness theo cường độ. Không tối ưu threshold trên test set.

**Những kết luận nào không được phép đưa ra?**

Không được nói STEGO là detector steganography tổng quát; không nói Sleepy Alarm hoạt động blind; không nói Blue 3 payload chắc chắn bị xóa sau JPEG/resize; không dùng FPR=0 từ tám mẫu synthetic để khẳng định không có false positive. Có thể khẳng định 22/22 tests pass theo quality-gate log ở revision a040e38; nếu thay source hoặc tests thì phải chạy lại, không dùng log cũ sáu test.

## 11. Trả lời ngắn gọn về điểm yếu

**Nếu phải chỉ ra một điểm yếu lớn nhất?**  
Đồ án chứng minh tốt khả năng giải hai challenge cụ thể, nhưng chưa chứng minh tính tổng quát. Đặc biệt detector audio có recall=0 và Sleepy Alarm cần reference.

**Nếu giảng viên yêu cầu chỉ ra đóng góp cá nhân?**  
Trình bày phần decoder đã tự triển khai, giả định và lỗi từng gặp, vì sao sửa kênh stereo/prefix/symbol window, rồi mở log và JSON để chứng minh. Không nhận phần creator source hoặc thuật toán gốc là phát minh của mình.

**Nếu được thêm một tuần?**  
Quality gate và ma trận BER/partial recovery hiện đã có kết quả. Phần công việc mới có giá trị nhất là corpus độc lập cho detector và blind/reference-free audio extraction, sau đó là robustness sweep trên nhiều challenge/cover. Đây là hướng nghiên cứu, không phải kết quả đã đạt.

## 12. Kiểm chứng artifact thật và metric partial recovery

**Vì sao cần integration test nếu đã có unit test synthetic?**

Unit test synthetic kiểm tra các thành phần trong môi trường kiểm soát. Integration test mới chạy Blue 3 và Sleepy Alarm trên đúng artifact được pin trong `data/`, kiểm tra SHA-256, flag đầy đủ, số symbol và separator. Nó phát hiện được lỗi do dữ liệu/codec thực tế mà fixture synthetic không mô phỏng được.

**BER trong ma trận audio được tính thế nào?**

Sau khi decoder tạo 350 nhãn symbol, script mới mã hóa chuỗi ground truth thành 312 bit và 38 separator rồi so sánh vị trí tương ứng. BER = số bit sai / 312; symbol error rate tính trên 350 vị trí. Separator precision/recall báo riêng lỗi thừa/thiếu separator. Ground truth chỉ được dùng ở bước chấm đầu ra, không phải đầu vào giải mã.

**Levenshtein edit distance trong Blue 3 có ý nghĩa gì?**

Script lấy candidate được tạo ở độ dài baseline flag, rồi so sánh với chuỗi gốc. Edit distance đếm số phép chèn, xóa, thay thế tối thiểu; normalized edit similarity = 1 - distance / độ dài lớn nhất. Nếu không có candidate ở độ dài đó, edit distance được để null, không giả vờ là đo được zero.

**Lệnh nào xác nhận revision có thể tái lập?**

Chạy `python scripts/verify_reproducibility.py`. Bằng chứng hiện có ghi 22/22 tests pass, hash ba artifact và hai decoder exact-match. JSON ghi source commit đã kiểm thử (`a040e38`); commit `3bb2b57` lưu các file kết quả sau lần chạy, không thay đổi source/tests. Nếu sửa source/tests, chạy gate lại trước khi nộp.

