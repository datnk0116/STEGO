# Kế hoạch nâng STEGO lên mục tiêu 9.6/10

## 1. Phạm vi và nguyên tắc chấm

Đối chiếu theo rubric UET.CN3124:
- Tiêu chí 1 — Lập kế hoạch và biện minh: 2,0 điểm (CLO5).
- Tiêu chí 2 — Triển khai và tài liệu hóa: 4,0 điểm (CLO4).
- Tiêu chí 3 — Phân tích kết quả: 2,0 điểm (CLO4).
- Tiêu chí 4 — Đánh giá, phản biện và tự học: 2,0 điểm (CLO5).

Mục tiêu 9,6/10 là **điểm mục tiêu có điều kiện**, không phải điểm được bảo đảm. Giảng viên vẫn có thể yêu cầu trình diễn lại decoder, chạy script và vấn đáp. Đánh giá này chỉ xét source, test, dữ liệu, log, kết quả JSON/CSV và tài liệu Markdown trong repository; không dùng thông tin cá nhân hoặc DOCX/PDF/ZIP để tính điểm.

Tài liệu học phần yêu cầu một chủ đề CTF nhất quán, khuyến nghị khoảng 30 giờ làm việc cá nhân, quy trình từng bước, bằng chứng trung gian, phần tùy biến/mở rộng, góc nhìn tấn công/phòng thủ và tự đánh giá. Logbook phải dựa trên hoạt động thật. Không điền giờ, ảnh chụp, thao tác hoặc trải nghiệm chưa thực hiện.

## 2. Chẩn đoán điểm nghẽn

| Hạng mục | Hiện trạng đã xác minh | Tác động tới điểm |
|---|---|---|
| Hai challenge chính thức | Blue 3 và Sleepy Alarm đều có decoder exact-match và artifact/hash | Điểm mạnh của CLO4 |
| Unit tests | Source cũ có 11 test methods; log cũ chỉ chứng minh 6 tests | Chưa đủ bằng chứng cho revision mới |
| Integration | Trước thay đổi chưa có test tự động chạy cả hai artifact chính thức | Có nguy cơ test synthetic pass nhưng artifact thật lỗi |
| Robustness ảnh | Chủ yếu có PASS/FAIL; chưa có mức khôi phục một phần | Phân tích kết quả chưa định lượng sâu |
| Robustness audio | 23 trial, 7 PASS; JSON cũ chưa có BER/symbol error từng trial | Chưa thấy được mức độ lỗi khi exact-match FAIL |
| Reproducibility | Có lệnh rời rạc nhưng chưa có một quality gate tổng hợp hash, environment, tests và decoder | Khó xác minh một revision từ đầu đến cuối |
| Detector | Ảnh F1=1 trên mẫu nhỏ cùng nguồn; audio recall=0 | Cần tiếp tục diễn giải trung thực, không được tuning trên test |
| Tự học/logbook | Có mô tả kỹ thuật và lịch sử debug, nhưng giờ bắt đầu/kết thúc còn trống | Chưa đủ bằng chứng cho quá trình học tập cá nhân |

## 3. Thay đổi đã triển khai trên main

### 3.1. Kiểm thử trên artifact chính thức

Đã thêm `tests/test_official_artifacts.py` với ba integration tests:
1. Kiểm tra SHA-256 của cả ba artifact challenge/reference.
2. Chạy Blue 3 trên PNG chính thức và xác nhận flag đầy đủ.
3. Chạy Sleepy Alarm trên MP3 chính thức với reference, xác nhận 350 symbol, 38 separator, 39 byte, không lỗi byte và exact-match.

### 3.2. Kiểm thử metric

Đã thêm `tests/test_robustness_metrics.py` và `src/experiments/robustness_metrics.py`:
- Blue 3: Levenshtein edit distance, character position accuracy và normalized edit similarity.
- Sleepy Alarm: bit error rate (BER), symbol error rate, separator precision và recall.
- Có test cho trường hợp chính xác, sai bit, thiếu separator, candidate thiếu và độ dài stream không hợp lệ.

Source dự kiến có 22 test methods: 11 test methods cũ + 3 integration tests + 8 metric tests. **Chưa tuyên bố 22 test đã pass** cho đến khi quality gate chạy trên máy của người thực hiện.

### 3.3. Nâng cấp robustness output

- `blue3_extended_robustness.py`: ghi thêm candidate ở độ dài baseline và metric khôi phục ký tự.
- `sleepy_alarm_robustness_matrix.py`: ghi BER, symbol error rate, separator precision/recall cho từng trial và tổng hợp trung bình.
- Output historical 1/9 và 7/23 không bị sửa ngược hoặc gán metric chưa đo. Cần chạy lại để sinh JSON/CSV mới.

### 3.4. Quality gate một lệnh

Đã thêm `scripts/verify_reproducibility.py` và `docs/QUALITY_GATE.md`. Quality gate:
- Chạy toàn bộ unittest suite.
- Kiểm tra số byte và SHA-256 của ba artifact.
- Chạy hai decoder trên artifact chính thức.
- Ghi reference-free result như một phép đo giới hạn, không coi thất bại reference-free là lỗi của quality gate.
- Ghi Git commit, branch, working-tree status, Python/package versions.
- Ghi kết quả ở `results/verification/quality-gate.json` và `results/logs/quality-gate-tests.log`.

### 3.5. Đồng bộ tài liệu

Đã cập nhật report, README và Q&A để giải thích integration testing, metric partial recovery và cách xác minh revision. Không viết detector audio thành công hơn thực tế; benchmark hiện tại vẫn là TP=0, FN=5 ở audio.

## 4. Mục tiêu điểm theo rubric

| Tiêu chí | Điểm mục tiêu | Điều kiện cần chứng minh |
|---|---:|---|
| 1. Lập kế hoạch và biện minh | 1,9/2,0 | Một chủ đề thống nhất; hai challenge bổ trợ; có RQ/giả thuyết; so sánh lựa chọn; nguồn rõ ràng |
| 2. Triển khai và tài liệu hóa | 3,9/4,0 | 22 tests pass tại commit cuối; hash ba artifact đúng; cả hai decoder exact-match; log/JSON ghi cùng revision; script tái chạy được |
| 3. Phân tích kết quả | 1,9/2,0 | Có BER, symbol error, separator precision/recall và character edit distance; giải thích cả PASS lẫn FAIL; không tổng quát hóa từ một artifact |
| 4. Đánh giá, phản biện và tự học | 1,9/2,0 | Threat model/validity/limitations rõ; phản biện đúng; trích nguồn minh bạch; logbook giờ thật và phản tư cá nhân có bằng chứng |
| **Tổng mục tiêu** | **9,6/10** | Chỉ có cơ sở nhắm tới sau khi hoàn thành các điều kiện bên dưới |

## 5. Kế hoạch nghiệm thu chi tiết

### P0 — Đồng bộ local với main và chạy quality gate

**Thao tác:** Pull code mới, chạy quality gate.

**Đạt khi:**
- 22 test methods chạy thành công.
- Ba artifact có SHA-256 khớp manifest.
- Blue 3 khôi phục đúng flag chính thức.
- Sleepy Alarm có reference đạt exact-match 39 ký tự, 350 symbol, 38 separator.
- JSON chất lượng và log test lưu được cùng commit SHA.

**Không đạt nếu:** bất kỳ hash sai, test fail, decoder không exact-match hoặc log không ghi revision.

### P1 — Tạo kết quả partial-recovery mới

**Thao tác:** Chạy lại Blue 3 extended robustness và Sleepy Alarm robustness matrix sau khi pull.

**Đạt khi:**
- CSV/JSON Blue 3 có candidate tại baseline length (nếu decoder tạo được), edit distance và normalized similarity; trường hợp không có candidate phải ghi unavailable/null.
- CSV/JSON audio có BER, symbol error rate, separator precision/recall cho đủ 23 trial.
- Baseline vẫn exact-match.
- Có thể giải thích vì sao một phép biến đổi làm exact-match FAIL nhưng vẫn còn/không còn khôi phục một phần.

**Lưu ý:** Không đặt mục tiêu phải tăng tỷ lệ PASS. Mục tiêu là đo và giải thích đúng.

### P2 — Đối chiếu report với output thực tế

**Thao tác:** Sau khi chạy P0/P1, so sánh:
- `results/verification/quality-gate.json`
- `results/logs/quality-gate-tests.log`
- `results/blue3/extended_robustness/extended_robustness.json`
- `results/sleepy_alarm/robustness_matrix/robustness_matrix.json`

Cập nhật số test, commit SHA, BER/edit-distance và thời gian chạy vào report chỉ theo output thật. Không chép số liệu historical nếu kết quả revision mới khác.

### P3 — Hoàn thiện logbook và phản tư cá nhân

**Thao tác thủ công bắt buộc:**
- Mở `results/logbook-template.csv`.
- Điền ngày, giờ bắt đầu/kết thúc, thời lượng, mục tiêu/giả thuyết, command, kết quả, bài học và đường dẫn bằng chứng từ lịch sử làm việc thật.
- Đảm bảo tổng thời lượng phản ánh khối lượng khoảng 30 giờ theo yêu cầu học phần. Nếu không thể xác minh một khoảng giờ, để trống và giải thích; không dựng số.
- Viết 3–5 đoạn phản tư cá nhân: kiến thức xuất phát, giả thuyết từng bị bác bỏ, tài liệu/API tự học, lần thất bại đáng nhớ, điều hiểu sâu hơn sau khi debug và kế hoạch học tiếp.
- Chuẩn bị khả năng giải thích lại từng phần code; repository là bài cá nhân và giảng viên có quyền yêu cầu trình diễn.

**Đạt khi:** logbook và reflection mô tả trải nghiệm thật, có đường dẫn evidence/commit phù hợp, không chỉ lặp lại nội dung do công cụ tạo.

### P4 — Commit bằng chứng kỹ thuật

Chỉ commit các file log/JSON/CSV mới sau khi kiểm tra:
- Kết quả được sinh từ revision hiện tại.
- Không sửa artifact gốc trong `data/`.
- Không thêm secrets hoặc file môi trường.
- Không stage DOCX/PDF/ZIP nếu phạm vi commit chỉ là bằng chứng kỹ thuật.
- Working tree và commit SHA được ghi trong quality-gate JSON.

## 6. Command nghiệm thu

Các command copy/paste đầy đủ được đặt ở câu trả lời triển khai cùng cuộc hội thoại. Tối thiểu cần chạy:

```bash
git pull --ff-only origin main
python scripts/verify_reproducibility.py
python src/experiments/blue3_extended_robustness.py data/blue3/blue.png
python src/experiments/sleepy_alarm_robustness_matrix.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
```

Sau khi kiểm tra các output, stage riêng các file `results/logs/quality-gate-tests.log`, `results/verification/quality-gate.json`, và các JSON/CSV robustness mới. Không commit kết quả chưa kiểm tra.

## 7. Rủi ro còn lại không thể giải bằng cách viết thêm tài liệu

1. Detector audio hiện recall=0. Muốn cải thiện phải có corpus độc lập và validation/test đúng cách; không hạ threshold chỉ để làm đẹp benchmark hiện tại.
2. Sleepy Alarm vẫn reference-assisted. Không gọi là blind decoding cho đến khi có một thuật toán không cần reference và có kiểm chứng độc lập.
3. Hai challenge là quy mô nhỏ. BER/partial-recovery giúp phân tích sâu hơn nhưng không biến chúng thành corpus đại diện.
4. Điểm 9,6 phụ thuộc vào chất lượng trình diễn và phản tư cá nhân. Không thể bảo đảm điểm số hoặc thay thế trải nghiệm thực tế bằng generated text.
