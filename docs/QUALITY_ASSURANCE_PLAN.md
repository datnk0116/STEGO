# Kế hoạch bảo đảm chất lượng và nghiệm thu STEGO

## 1. Phạm vi chấm và nguyên tắc

Đối chiếu rubric UET.CN3124:
- Tiêu chí 1 — Lập kế hoạch và biện minh: 2,0 điểm (CLO5).
- Tiêu chí 2 — Triển khai và tài liệu hóa: 4,0 điểm (CLO4).
- Tiêu chí 3 — Phân tích kết quả: 2,0 điểm (CLO4).
- Tiêu chí 4 — Đánh giá, phản biện và tự học: 2,0 điểm (CLO5).

Kế hoạch này đặt tiêu chí nghiệm thu ở mức cao nhất của rubric, tập trung vào tính đúng đắn, khả năng tái lập, chất lượng bằng chứng và phản biện kỹ thuật. Source, tests, dữ liệu challenge, kết quả JSON/CSV, log kỹ thuật và báo cáo Markdown là các lớp bằng chứng liên kết với nhau. DOCX/PDF/ZIP, thông tin hành chính và logbook là các hạng mục hoàn thiện hồ sơ riêng, vẫn phải được kiểm tra trước khi nộp. Không tự chấm điểm thay giảng viên; không suy diễn trải nghiệm cá nhân hoặc thời lượng làm việc từ commit.

Rubric mức Xuất sắc đòi hỏi: có tư duy thiết kế và so sánh phương án; tài liệu hóa sâu, quy trình đáng tin cậy và tái hiện được; phân tích chặt chẽ cả rủi ro/dấu hiệu phát hiện/biện pháp khắc phục; đánh giá chín chắn, có nguồn và chỉ ra hướng học tiếp.

## 2. Trạng thái repository đã xác minh

**Repository:** datnk0116/STEGO  
**Branch:** main  
**Revision được quality gate ghi nhận:** a040e3863145038b786ba6719629e636fdf2e565  
**Commit đóng gói log/JSON verification:** 3bb2b57790d164a6997ee1afe157a0fc7a8a8807

Commit 3bb2b57 là commit duy nhất sau revision a040e38; diff chỉ gồm hai tệp bằng chứng quality gate (log và JSON), không thay đổi source hoặc tests. Vì vậy JSON ghi revision được kiểm thử trước khi chính các tệp kết quả được commit.

| Hạng mục | Bằng chứng hiện hành | Trạng thái |
|---|---|---|
| Unit/integration tests | 22/22 pass, exit code 0; log quality-gate-tests.log | Đã đạt |
| Artifact integrity | 3/3 file đúng byte size và SHA-256 | Đã đạt |
| Blue 3 chính thức | Exact-match flag 50 ký tự; 49 candidate attempts | Đã đạt |
| Sleepy Alarm chính thức | Reference-assisted exact-match; 350 symbol, 38 separator, 39 byte, 0 byte errors | Đã đạt |
| Sleepy Alarm reference-free | 350 symbol, 49 separator, 26 ký tự; format invalid, exact-match fail | Giới hạn đã đo và công khai |
| Blue 3 extended robustness | 9 biến thể, 1 exact-match; partial character metrics có trong JSON/CSV | Đã đạt |
| Sleepy Alarm robustness matrix | 23 trial, 7 exact-match; BER/SER/separator metrics có trong JSON/CSV | Đã đạt |
| Steganalysis benchmark | Image TP=5/TN=12/FP=0/FN=0; audio TP=0/TN=8/FP=0/FN=5 | Đã đo; giới hạn rõ |
| Phân tích và phản biện | Có RQ/giả thuyết, threat model, validity, tấn công/phòng thủ, limitations và next experiments | Đã đồng bộ với evidence |

Lưu ý: results/logs/unit-tests.log là log lịch sử sáu test, không phải bằng chứng hiện hành. Bằng chứng 22/22 nằm trong results/logs/quality-gate-tests.log và results/verification/quality-gate.json.

## 3. Các hạng mục đã triển khai

### P0 — Xác minh baseline và tính tái lập: HOÀN TẤT

Quality gate scripts/verify_reproducibility.py đã:
1. Chạy python -m unittest discover -s tests -v.
2. Xác nhận 22 test methods đã chạy đúng số lượng và đều pass.
3. Kiểm tra kích thước và SHA-256 của ba artifact chính thức.
4. Chạy Blue 3 và Sleepy Alarm reference-assisted trên artifact gốc.
5. Ghi Git commit, branch, trạng thái working tree, hệ điều hành, Python và package versions.
6. Lưu JSON và log.

Kết quả đã commit:
- results/verification/quality-gate.json
- results/logs/quality-gate-tests.log

### P1 — Định lượng partial recovery: HOÀN TẤT

Blue 3:
- src/experiments/robustness_metrics.py bổ sung Levenshtein edit distance, position accuracy và normalized edit similarity.
- Candidate thiếu được ghi null cho edit distance, không bị tính sai thành khoảng cách 0.
- results/blue3/extended_robustness/extended_robustness.json và CSV có 9 biến thể và metrics từng biến thể.

Sleepy Alarm:
- Đã bổ sung bit error rate (BER), symbol error rate (SER), separator precision và recall theo từng trial.
- Ground truth chỉ được sử dụng sau extraction để chấm symbol stream; không được dùng để tạo payload trong decoder.
- results/sleepy_alarm/robustness_matrix/robustness_matrix.json và CSV có đủ 23 trial và aggregate metrics.

### P2 — Đồng bộ tài liệu với bằng chứng: HOÀN TẤT TRONG REVISION NÀY

Các tài liệu đã được đồng bộ:
- report/REPORT.md: summary, test evidence, robustness metrics, limitations, future work và conclusion.
- README.md: quality gate hiện tại, kết quả partial recovery, detector failure và reference-free failure.
- docs/QUALITY_GATE.md: phân biệt source commit được test với commit đóng gói output.
- docs/DEFENSE_QA.md: câu trả lời vấn đáp nêu đúng 22/22 test, các metric mới và các giới hạn còn lại.
- results/README.md: các output đã commit không còn bị đánh dấu pending.
- docs/QUALITY_ASSURANCE_PLAN.md: phân biệt việc đã hoàn tất và hướng nghiên cứu còn mở.

Không ghi lại kết quả lịch sử thành kết quả mới; không diễn giải metric như hiệu năng của quần thể.

## 4. Diễn giải kết quả định lượng phải thống nhất

### 4.1. Blue 3

Ma trận có 9 phép biến đổi và 1/9 exact-match. Tuy nhiên, exact-match không mô tả hết partial recovery:

| Biến thể | Position accuracy | Edit distance | Normalized similarity |
|---|---:|---:|---:|
| Brightness 0,9 | 94% (47/50) | 3 | 94% |
| Brightness 1,1 | 56% (28/50) | 20 | 60% |
| Contrast 0,9 | 0% theo vị trí | 48 | 4% |
| Contrast 1,1 | 0% | 50 | 0% |
| Gaussian blur 0,3 | 100% | 0 | 100% |
| Crop 16 px | 0% | 50 | 0% |
| Gaussian noise sigma 0,5 | Không có candidate độ dài baseline | null | 0% |
| Gaussian noise sigma 1,0 | Không có candidate độ dài baseline | null | 0% |
| Gaussian noise sigma 2,0 | 0% | 50 | 0% |

Tám trường hợp không exact-match không đồng nghĩa tám trường hợp đều không tạo candidate: sáu trường hợp có chuỗi độ dài 50 để đo lỗi ký tự; hai trường hợp noise sigma 0,5 và 1,0 không có candidate ở độ dài baseline. Đây là khác biệt quan trọng cần nêu khi bảo vệ.

### 4.2. Sleepy Alarm

Ma trận mở rộng có 23 trial, 7 exact-match (bao gồm baseline). Các aggregate là trung bình số học không trọng số của metric theo trial, có tính baseline:
- Mean symbol error rate: 12,31%.
- Mean bit error rate: 12,97%.
- Mean separator precision: 77,07%.
- Mean separator recall: 93,14%.

Một vài trường hợp để giải thích:
- Baseline: BER=0, SER=0, 38/38 separator.
- Target AWGN 20 dB: SER=20,57%, BER=22,76%.
- Target AWGN 10 dB: SER=55,14%, BER=57,37%.
- Reference AWGN 20 dB: SER=27,43%, BER=30,77%.
- Reference AWGN 10 dB: SER=60,00%, BER=63,78%.

Không được gọi những giá trị mean này là hiệu năng trên mọi audio; chúng chỉ tóm tắt 23 trial trên một cặp file challenge cụ thể. Paired robustness (4/4), asymmetric robustness (3/6) và extended matrix (7/23) là ba nhóm thử nghiệm khác điều kiện, không được gộp thành một tỷ lệ.

### 4.3. Steganalysis detector

Benchmark hiện tại:
- Image: TP=5, TN=12, FP=0, FN=0.
- Audio: TP=0, TN=8, FP=0, FN=5; recall=0, F1=0.

Positive là các biến thể từ một artifact chính thức mỗi modality; benign controls là synthetic. Do đó image F1=1 không chứng minh generalization. Audio recall=0 là một thất bại thực nghiệm cần giữ nguyên, không hạ threshold bằng cách nhìn vào cùng test set. Muốn cải thiện phải có corpus độc lập, validation để chọn feature/threshold và held-out test chỉ dùng một lần.

### 4.4. Threat model

- Blue 3: decoder sử dụng giả định về generator và cấu trúc vùng của challenge; không đại diện một blind detector phổ quát.
- Sleepy Alarm: kết quả thành công hiện là reference-assisted; reference-free đã chạy nhưng thất bại. Không được gọi Sleepy Alarm là blind decoding.
- Correlation gần 1 chỉ hỗ trợ ước lượng alignment, không bảo đảm scale của hai track tương thích hoặc phân loại ASK đúng.

## 5. Tiêu chí nghiệm thu theo rubric

| Tiêu chí | Bằng chứng hiện có | Điều kiện hoàn thiện cuối |
|---|---|---|
| Lập kế hoạch và biện minh | Phạm vi hai challenge cùng chủ đề; RQ/H1–H3; so sánh phương án; nguồn gốc artifact và lý do lựa chọn | Giữ các giả định và giới hạn lựa chọn nhất quán trong report/README |
| Triển khai và tài liệu hóa | Decoder hai challenge; 22/22 test ở gate đã ghi nhận; 3/3 hash đúng; kết quả JSON/CSV và log | Chạy gate trên working copy cuối; build PDF/ZIP; kiểm tra ZIP có đủ source, tests, script, data, report Markdown và evidence |
| Phân tích kết quả | Exact-match, partial recovery, BER/SER, separator metrics, confusion matrix và phân tích failure | Không nâng kết luận vượt khỏi hai challenge và các phép biến đổi đã thử |
| Đánh giá, phản biện và tự học | Threat model, validity, detector failure, reference dependency, robustness limits và hướng nghiên cứu tiếp | Phần phản tư cá nhân/logbook chỉ hoàn thiện từ ghi chú và trải nghiệm thật; không suy diễn từ commit hoặc tự tạo thời lượng |

Bảng này là checklist chất lượng dựa trên rubric, không phải tự chấm điểm. Kết quả đánh giá chính thức thuộc về giảng viên.

## 6. Công việc trước khi đóng gói nộp

| Ưu tiên | Công việc | Điều kiện nghiệm thu |
|---|---|---|
| P0 | Chạy `python scripts/verify_reproducibility.py` trên working copy cuối | Exit code 0; 22/22 test; ba hash đúng; hai decoder exact-match trong điều kiện đã mô tả |
| P0 | Chạy `python scripts/build_submission.py` | DOCX/PDF được sinh từ report Markdown hiện tại; PDF qua kiểm tra số trang; ZIP được tạo và mở/kiểm tra được |
| P0 | Kiểm tra nội dung ZIP | Có README, source, tests, scripts, workflow, dữ liệu gốc, kết quả, báo cáo Markdown, references và docs; không có .venv, .git, file tạm hoặc ZIP lồng |
| P1 | Hoàn thiện trang bìa và tên file | Thay các trường hành chính bằng thông tin đúng; dùng tên file nhất quán theo hướng dẫn môn học |
| P1 | Hoàn thiện phản tư/logbook | Chỉ ghi những gì người thực hiện xác nhận từ ghi chú thực tế; để trống thời gian không xác định được thay vì dựng lại |
| Khi được yêu cầu | Giải thích và tái hiện quy trình | Có thể mở source, nêu giả định, chạy lệnh và giải thích các giới hạn; không cần chuẩn bị thành bài thuyết trình nếu không được yêu cầu |

Các nghiên cứu về detector đa nguồn, reference-free Sleepy Alarm và robustness trên nhiều challenge là hướng phát triển tiếp theo, không được trình bày như kết quả đã hoàn thành.
## 7. Command kiểm tra local cuối cùng

Từ thư mục repository:

~~~bash
git status --short
git pull --ff-only origin main
git log -1 --oneline
python scripts/verify_reproducibility.py
~~~

Kiểm tra kết quả gate:

~~~bash
python - <<'PY'
import json
from pathlib import Path

p = Path("results/verification/quality-gate.json")
data = json.loads(p.read_text(encoding="utf-8"))

tests = data["unit_tests"]
artifacts = data["artifact_integrity"]
decoders = data["official_decoder_verification"]

print("Tested source commit:", data["git"]["commit"])
print("Tests:", tests["tests_run"], "/", tests["expected_test_methods"])
print("Tests passed:", tests["passed"])
print("Artifacts:", {name: item["passed"] for name, item in artifacts.items()})
print("Blue 3 exact:", decoders["blue3"]["exact_match"])
print("Sleepy Alarm exact:", decoders["sleepy_alarm_reference_assisted"]["exact_match"])
print("Overall:", data["overall_passed"])

assert tests["tests_run"] == tests["expected_test_methods"] == 22
assert tests["passed"]
assert all(item["passed"] for item in artifacts.values())
assert decoders["blue3"]["exact_match"]
assert decoders["sleepy_alarm_reference_assisted"]["exact_match"]
assert data["overall_passed"]
print("LOCAL QUALITY GATE: PASS")
PY
~~~

Nếu command này pass, không cần chạy GitHub Actions. Nếu quality gate tạo thay đổi mới trong working tree, xem xét trước khi commit:

~~~bash
git status --short
git diff -- results/verification/quality-gate.json results/logs/quality-gate-tests.log
~~~

Chỉ commit hai file gate nếu chúng thực sự được tái tạo từ local run và bạn muốn lưu bằng chứng môi trường local:

~~~bash
git add results/verification/quality-gate.json results/logs/quality-gate-tests.log
git diff --cached --stat
git commit -m "test: record local reproducibility verification"
git push origin main
~~~

Nếu gate thất bại, không commit log như bằng chứng đạt; giữ nguyên output lỗi để xác định nguyên nhân trước.