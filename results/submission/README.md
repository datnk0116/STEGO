# Submission package

## Trạng thái tại HEAD được kiểm tra

- Repository: `datnk0116/STEGO`, branch `main`
- HEAD: `a62c717f36d22e478b767c6917f2bc4362d75667`
- Trạng thái: **NOT_VERIFIED** — ba binary đang được Git track nhưng chưa có manifest chứng minh chúng được build từ cùng một input revision và vượt qua toàn bộ kiểm tra sau lần cập nhật report gần nhất.

Các thông tin hiện đọc được từ Git tree và PDF metadata:

| Artifact | Byte size hiện track | Thông tin PDF metadata | Kết luận |
|---|---:|---|---|
| `STUDENT_UETCN3124_CTF_Report.docx` | 222,872 | Chưa có SHA-256/build provenance được xác nhận | Chưa xác minh |
| `STUDENT_UETCN3124_CTF_Report.pdf` | 727,110 | 19 trang tổng; metadata File size = 727,110 bytes; CreationDate = 2026-11-14 19:35:54 +07 | Kích thước khớp metadata, chưa chứng minh cùng report source |
| `STUDENT_UETCN3124_Scripts.zip` | 2,697,114 | Chưa chạy `unzip -t` trên binary hiện tại | Chưa xác minh |

`pdf-metadata.txt` khớp byte size PDF trong Git tree; nhận định cũ rằng metadata là 711,994 bytes đã lỗi thời. Metadata ghi PDF có 19 trang tổng; cần chạy page checker để xác định số trang thân bài, sau đó kiểm tra trực quan. Không được suy ra pass chỉ từ metadata hoặc sự tồn tại của file.

## Build input và package freshness

`package-manifest.json` phân biệt:
- `build_input_commit`: source revision mà DOCX/PDF/ZIP được tạo từ.
- Commit lưu binary và manifest: commit hậu kỳ, dự kiến chỉ thêm/cập nhật output thuộc `results/submission/`.

Không ghi commit chứa chính manifest vào trong manifest. Freshness được xác định bằng cách kiểm tra build input commit là ancestor của HEAD và không có source/report/dependency changes sau revision đó. Thay đổi đối với binary và manifest được phép ở commit lưu package; thay đổi đầu vào làm package STALE.

## Reference template và file tạm

- `reference.docx` là Pandoc/Word reference template được tạo bởi `scripts/create_reference_docx.py`.
- `report-pandoc.docx` và `report-fixed.docx` là file trung gian; build script xóa chúng sau khi build thành công.
- ZIP loại trừ toàn bộ `results/submission/`, ZIP lồng, DOCX/PDF submission, cache, file tạm và file môi trường.

## Quy tắc trang báo cáo

Tài liệu hướng dẫn học phần ở trang 6 viết phần nội dung chính **“không nên vượt quá 15 trang”**; cách diễn đạt này là khuyến nghị, không phải câu “bắt buộc không vượt quá”. Theo yêu cầu hiện tại, repository giữ báo cáo 17 trang nội dung; checker dùng ceiling cục bộ 20 trang và không cắt nội dung khoa học. Nếu giảng viên/Canvas có thông báo riêng ghi giới hạn bắt buộc thì ưu tiên thông báo đó.

## Quy trình build và nghiệm thu cục bộ

Sau khi pull/checkout source revision cuối cùng và bảo đảm working tree sạch:

```bash
python scripts/build_submission.py --max-main-pages 20
```

Mở PDF vừa tạo, kiểm tra font, công thức, hình, bảng, ngắt trang và header/footer; sau đó ghi nhận kiểm tra trực quan:

```bash
python scripts/check_submission_manifest.py --confirm-pdf-visual-inspection
git add results/submission/
git commit -m "build: verify final submission package"
python scripts/check_submission_manifest.py --require-verified
python scripts/check_provenance_consistency.py --require-submission-package
```

Build script ghi build input commit, UTC timestamp, command, tool versions, SHA-256, byte size, số trang PDF, page checker result, `unzip -t` result và ZIP inventory. Manifest chỉ chuyển `VERIFIED` sau khi PDF được kiểm tra trực quan. Nếu có thay đổi source, tests, data, dependencies hoặc report sau `build_input_commit`, phải build lại; không chỉ cập nhật hash thủ công.

## Thành phần ZIP bắt buộc

ZIP phải có README, requirements, report, source, tests, data, scripts, references, docs và result evidence. Không có file tạm/cache, ZIP lồng, DOCX/PDF submission hoặc thư mục `results/submission/`. Checker kiểm tra required paths, archive integrity và input freshness.
