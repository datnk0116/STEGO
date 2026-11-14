# Kế hoạch bảo đảm chất lượng và nghiệm thu STEGO

<!-- PROVENANCE_STATUS_START -->
**Verification provenance:** The canonical run record is results/verification/provenance.json. tested_commit identifies the source revision actually executed. The evidence-packaging commit and current HEAD are derived from Git history by scripts/check_provenance_consistency.py; they are not copied into this snapshot. Documentation-only changes do not stale the technical gate. Changes to source, tests, challenge data, dependencies, artifact manifest, or gate implementation do. Submission-package freshness is assessed separately.
<!-- PROVENANCE_STATUS_END -->


## 1. Phạm vi chấm và nguyên tắc

Đối chiếu rubric UET.CN3124:
- Tiêu chí 1 — Lập kế hoạch và biện minh: 2,0 điểm (CLO5).
- Tiêu chí 2 — Triển khai và tài liệu hóa: 4,0 điểm (CLO4).
- Tiêu chí 3 — Phân tích kết quả: 2,0 điểm (CLO4).
- Tiêu chí 4 — Đánh giá, phản biện và tự học: 2,0 điểm (CLO5).

Kế hoạch này đặt tiêu chí nghiệm thu ở mức cao nhất của rubric, tập trung vào tính đúng đắn, khả năng tái lập, chất lượng bằng chứng và phản biện kỹ thuật. Source, tests, dữ liệu challenge, kết quả JSON/CSV, log kỹ thuật và báo cáo Markdown là các lớp bằng chứng liên kết với nhau. DOCX/PDF/ZIP, thông tin hành chính và logbook là các hạng mục hoàn thiện hồ sơ riêng, vẫn phải được kiểm tra trước khi nộp. Không tự chấm điểm thay giảng viên; không suy diễn trải nghiệm cá nhân hoặc thời lượng làm việc từ commit.

Backlog sửa repository theo từng file, thứ tự phụ thuộc và điều kiện nghiệm thu được duy trì tại [docs/IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md).

Rubric mức Xuất sắc đòi hỏi: có tư duy thiết kế và so sánh phương án; tài liệu hóa sâu, quy trình đáng tin cậy và tái hiện được; phân tích chặt chẽ cả rủi ro/dấu hiệu phát hiện/biện pháp khắc phục; đánh giá chín chắn, có nguồn và chỉ ra hướng học tiếp.

## 2. Trạng thái provenance và bằng chứng đã ghi nhận

**Repository:** datnk0116/STEGO  
**Canonical record:** results/verification/provenance.json  
**Latest tested revision:** `38fbecab7aea8c241243fb50d044aea90ab657f7`; **evidence-packaging revision:** `29c7e9e8e98d96e20e5172a63a359cfefd22edcc`. Current HEAD được suy ra bằng strict checker, không hardcode trong snapshot.

Baseline trước khi bổ sung provenance tooling (giữ nguyên như lịch sử):
- 22/22 test methods pass, exit code 0.
- Ba artifact chính thức đúng byte size và SHA-256.
- Blue 3 exact-match.
- Sleepy Alarm reference-assisted exact-match.
- Sleepy Alarm reference-free chưa exact-match (26 ký tự, 49 separator).

Bản migration provenance đánh dấu pre-run working-tree status của snapshot lịch sử là **không được ghi nhận**; không suy diễn trạng thái ban đầu từ trường status được chụp sau khi gate đã ghi log.

**Latest generated-run evidence (14 November 2026):** `results/verification/quality-gate.json` và `results/logs/quality-gate-tests.log` ghi nhận 38/38 test methods pass, exit code 0, runtime 5.358 giây; 3/3 artifact đúng byte size/SHA-256; Blue 3 exact-match; Sleepy Alarm reference-assisted exact-match. Tested commit: `38fbecab7aea8c241243fb50d044aea90ab657f7`; branch `main`; evidence-packaging commit: `29c7e9e8e98d96e20e5172a63a359cfefd22edcc`. Pre-run working tree được capture clean với status rỗng. Sleepy Alarm reference-free vẫn thất bại (26 ký tự, 49 separator) và không phải điều kiện PASS của gate.

Sau lần chạy này, thay đổi đang thực hiện chỉ thuộc tài liệu; các chỉnh sửa docs-only không làm stale technical gate theo thiết kế checker. Tuy nhiên, cần chạy unit suite và strict provenance checker trên checkout sau khi pull commit tài liệu để xác nhận status blocks/current HEAD. Không cần chạy lại ma trận robustness hoặc full quality gate chỉ để refresh tài liệu. Chỉ chạy lại full gate khi source, tests, challenge data, dependencies, manifest hoặc gate implementation thay đổi.

| Hạng mục | Baseline lịch sử | Evidence mới nhất |
|---|---|---|
| Unit/integration tests | 22/22 pass | **38/38 pass**, exit code 0, 5.358 s |
| Artifact integrity | 3/3 SHA-256 pass | **3/3** byte size/SHA-256 pass |
| Official decoders | Blue 3 và Sleepy Alarm reference-assisted exact-match | Cả hai tiếp tục **exact-match** |
| Provenance | Pre-run status không được ghi nhận | Generated snapshot; pre-run clean; tested/evidence commits được ghi và suy ra bằng checker |
| Submission package | Chưa xác minh nội dung/build input | **NOT_VERIFIED**; vẫn cần rebuild và kiểm tra riêng |

`results/logs/unit-tests.log` chỉ là log sáu test lịch sử. `results/logs/quality-gate-tests.log` là log tương ứng với JSON 38/38 hiện hành; số test của các lần chạy khác phải lấy từ JSON/log đúng cặp, không hardcode.

## 3. Các hạng mục đã triển khai

### P0 — Xác minh baseline và tính tái lập: HOÀN TẤT

Quality gate scripts/verify_reproducibility.py đã:
1. Chạy python -m unittest discover -s tests -v.
2. Xác nhận test methods đã chạy đúng số lượng được đếm động từ source và đều pass.
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

### P2 — Đồng bộ tài liệu với bằng chứng: status blocks đã chuẩn hóa; cần nghiệm thu bằng checker

Các tài liệu đã được đồng bộ:
- report/REPORT.md: summary, test evidence, robustness metrics, limitations, future work và conclusion.
- README.md: quality gate hiện tại, kết quả partial recovery, detector failure và reference-free failure.
- docs/QUALITY_GATE.md: phân biệt source commit được test với commit đóng gói output.
- docs/DEFENSE_QA.md: câu trả lời vấn đáp nêu gate mới nhất 38/38 test, phân biệt baseline 22/22 lịch sử, các metric mới và giới hạn còn lại.
- results/README.md: latest gate được mô tả theo đúng 38/38 JSON/log; baseline 22/22 và log sáu test được giữ ở vai trò lịch sử.
- docs/QUALITY_ASSURANCE_PLAN.md: phân biệt việc đã hoàn tất và hướng nghiên cứu còn mở.

Không ghi lại kết quả lịch sử thành kết quả mới; không diễn giải metric như hiệu năng của quần thể. Các status blocks canonical không bị sửa; strict checker phải được chạy trên checkout sau commit tài liệu.

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

Positive là các biến thể từ một artifact chính thức mỗi modality; benign controls là synthetic. Do đó image F1=1 không chứng minh generalization. Audio recall=0 là một thất bại thực nghiệm cần giữ nguyên. Feature-level audit cho thấy carrier-band ratio của positive xấp xỉ 0,000204, dưới ngưỡng 0,02 khoảng 98 lần, trong khi block-RMS CV xấp xỉ 0,987 vượt ngưỡng 0,15. Vì classifier dùng điều kiện AND, toàn bộ positive bị loại ở carrier-band feature. Feature này được tính trên toàn bộ track ~10,019 s dù ASK payload theo challenge dài 7 s; khả năng cửa sổ toàn track làm pha loãng tỷ lệ năng lượng là giả thuyết cần ablation, không phải nguyên nhân đã được chứng minh. Không tune threshold trên cùng test set; cần corpus độc lập, split theo nguồn, validation cho feature/threshold và held-out test.

### 4.4. Threat model

- Blue 3: decoder sử dụng giả định về generator và cấu trúc vùng của challenge; không đại diện một blind detector phổ quát.
- Sleepy Alarm: kết quả thành công hiện là reference-assisted; reference-free đã chạy nhưng thất bại. Không được gọi Sleepy Alarm là blind decoding.
- Correlation gần 1 chỉ hỗ trợ ước lượng alignment, không bảo đảm scale của hai track tương thích hoặc phân loại ASK đúng.

## 5. Tiêu chí nghiệm thu theo rubric

| Tiêu chí | Bằng chứng hiện có | Điều kiện hoàn thiện cuối |
|---|---|---|
| Lập kế hoạch và biện minh | Phạm vi hai challenge cùng chủ đề; RQ/H1–H3; so sánh phương án; nguồn gốc artifact và lý do lựa chọn | Giữ các giả định và giới hạn lựa chọn nhất quán trong report/README |
| Triển khai và tài liệu hóa | Decoder hai challenge; gate mới nhất 38/38 tests pass; 3/3 hash đúng; JSON/CSV/log/provenance | Chạy unit tests và strict checker trên checkout cuối; build PDF/ZIP; kiểm tra ZIP có đủ source, tests, script, data, report Markdown và evidence |
| Phân tích kết quả | Exact-match, partial recovery, BER/SER, separator metrics, confusion matrix và phân tích failure | Không nâng kết luận vượt khỏi hai challenge và các phép biến đổi đã thử |
| Đánh giá, phản biện và tự học | Threat model, validity, detector failure, reference dependency, robustness limits và hướng nghiên cứu tiếp | Phần phản tư cá nhân/logbook chỉ hoàn thiện từ ghi chú và trải nghiệm thật; không suy diễn từ commit hoặc tự tạo thời lượng |

Bảng này là checklist chất lượng dựa trên rubric, không phải tự chấm điểm. Kết quả đánh giá chính thức thuộc về giảng viên.

## 6. Công việc trước khi đóng gói nộp

| Ưu tiên | Công việc | Điều kiện nghiệm thu |
|---|---|---|
| P0 | Xác nhận 38/38 gate hiện hành bằng JSON/log và chạy strict provenance checker sau pull | JSON/log nhất quán; strict checker PASS; working tree sạch. Chỉ rerun `verify_reproducibility.py` nếu có thay đổi kỹ thuật làm stale gate |
| P0 | Chạy `python scripts/build_submission.py --max-main-pages 17` sau khi report chốt | DOCX/PDF được sinh từ report Markdown hiện tại; PDF qua checker nội bộ tối đa 17 trang phần thân (nếu hướng dẫn môn học áp dụng giới hạn 15 trang bắt buộc, cần rút xuống 15 trước khi nộp); ZIP được tạo và mở/kiểm tra được |
| P0 | Kiểm tra nội dung ZIP | Có README, source, tests, scripts, workflow, dữ liệu gốc, kết quả, báo cáo Markdown, references và docs; không có .venv, .git, file tạm hoặc ZIP lồng |
| P1 | Hoàn thiện trang bìa và tên file | Thay các trường hành chính bằng thông tin đúng; dùng tên file nhất quán theo hướng dẫn môn học |
| P1 | Hoàn thiện phản tư/logbook | Chỉ ghi những gì người thực hiện xác nhận từ ghi chú thực tế; để trống thời gian không xác định được thay vì dựng lại |
| Khi được yêu cầu | Giải thích và tái hiện quy trình | Có thể mở source, nêu giả định, chạy lệnh và giải thích các giới hạn; không cần chuẩn bị thành bài thuyết trình nếu không được yêu cầu |

Các nghiên cứu về detector đa nguồn, reference-free Sleepy Alarm và robustness trên nhiều challenge là hướng phát triển tiếp theo, không được trình bày như kết quả đã hoàn thành.
## 7. Command kiểm tra local cuối cùng

Từ thư mục repository sau khi pull commit tài liệu. Vì patch này chỉ sửa tài liệu, không cần chạy lại benchmark hoặc full gate; trước hết kiểm tra unit suite và provenance của evidence đã có:

~~~bash
git status --short --branch
git pull --ff-only origin main
git status --short --branch
python -m unittest discover -s tests -v
python scripts/check_provenance_consistency.py
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

assert tests["tests_run"] == tests["expected_test_methods"]
assert tests["passed"]
assert all(item["passed"] for item in artifacts.values())
assert decoders["blue3"]["exact_match"]
assert decoders["sleepy_alarm_reference_assisted"]["exact_match"]
assert data["overall_passed"]
print("RECORDED QUALITY GATE: PASS")
PY
~~~

Đối với thay đổi source/tests/data/dependencies/gate implementation trong tương lai, chạy full gate và commit cả ba output thành một snapshot:

~~~bash
python scripts/verify_reproducibility.py
git diff -- results/logs/quality-gate-tests.log results/verification/quality-gate.json results/verification/provenance.json
git add results/logs/quality-gate-tests.log results/verification/quality-gate.json results/verification/provenance.json
git commit -m "test: record local provenance verification"
python scripts/check_provenance_consistency.py
~~~

Sau khi hoàn thiện nội dung báo cáo, build và kiểm tra riêng gói nộp; trạng thái package hiện vẫn NOT_VERIFIED:

~~~bash
python scripts/build_submission.py --max-main-pages 17
python scripts/check_report_pdf.py results/submission/STUDENT_UETCN3124_CTF_Report.pdf --max-main-pages 17
unzip -l results/submission/STUDENT_UETCN3124_Scripts.zip
~~~

Nếu unit tests hoặc provenance checker thất bại, không sửa JSON/log để làm cho PASS; giữ nguyên output để xác định nguyên nhân. Không cần chạy GitHub Actions.
