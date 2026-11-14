# BÁO CÁO ĐỒ ÁN THỰC HÀNH CTF JEOPARDY
## UET.CN3124 — An toàn và an ninh mạng

**Tên đề tài:** Phân tích và đánh giá kỹ thuật ẩn tin trên ảnh và âm thanh qua Blue 3 (BYUCTF) và Sleepy Alarm (ImaginaryCTF 2024)  
**Chủ đề CTF chính:** Steganography  
**Sinh viên:** ______________________________ — **MSSV:** __________________  
**Lớp:** __________________ — **Ngày nộp:** ____ / ____ / 2026 — **Hạn nộp:** ____ / ____ / 2026

> **Sidenote hành chính:** Các trường thông tin cá nhân trên trang bìa hiện chưa được điền trong repository. Theo phạm vi rà soát kỹ thuật hiện tại, các trường này được xem là phần hành chính cần bổ sung khi xuất bản nộp bài, không dùng để đánh giá mức độ hoàn thành kỹ thuật của đồ án.

> **Trạng thái bằng chứng kỹ thuật:** Quality gate đã chạy thành công trên macOS 15.7.4/arm64/Python 3.14.10 tại source commit `11cd5e3216e779b6101b22cd891689ecdf9b8e54`: **22/22 test pass**, ba artifact khớp kích thước và SHA-256, Blue 3 exact-match và Sleepy Alarm reference-assisted exact-match (350 symbol, 38 separator, 39 byte). Commit `3015d5ddcab12fb99d53158c4029750d7b8805b3` lưu log/JSON quality gate và các ma trận robustness mới; commit này chỉ bổ sung bằng chứng, không thay đổi source hoặc tests. Kết quả reference-free Sleepy Alarm vẫn thất bại (26 ký tự, 49 separator); detector audio có recall=0. Các giới hạn này được giữ nguyên trong đánh giá.

---

## Tóm tắt

Đồ án khảo sát hai cơ chế steganography khác nhau trong cùng một chủ đề CTF. Blue 3 (BYUCTF) ẩn từng ký tự trong tổng sai khác giá trị RGB của các vùng vuông nằm trên đường chéo ảnh. Sleepy Alarm (ImaginaryCTF 2024) nhúng chuỗi bit bằng điều chế biên độ ASK trên sóng mang 8 kHz, tốc độ 50 baud, rồi trộn tín hiệu này vào bản nhạc báo thức.

Đối với Blue 3, công cụ tự viết phân tích ảnh PNG 512 × 512, suy luận màu nền RGB (64, 77, 205), thử 49 độ dài ứng viên và khôi phục chính xác flag 50 ký tự. Đối với Sleepy Alarm, decoder căn chỉnh hai MP3 bằng cross-correlation, bảo toàn prefix chưa chồng lấp, phân tích kênh trái và dùng coherent sine/cosine projection trên từng cửa sổ 882 mẫu. Kết quả trên MP3 chính thức gồm 350 symbol, 38 separator, 39 byte và chuỗi 39 ký tự trùng toàn bộ bitmap ground truth của creator. Bốn thí nghiệm audio robustness theo cặp target/reference đều khôi phục chính xác thông điệp; trong sáu phép biến đổi bất đối xứng, ba phép PASS và ba phép FAIL.

Đóng góp của đồ án gồm decoder Blue 3 có chế độ tự suy luận màu nền, decoder ASK có căn chỉnh tham chiếu và xác minh exact-match, công cụ tạo hình phân tích ảnh/âm thanh, bộ kiểm thử hồi quy tổng hợp, benchmark steganalysis heuristic và các ma trận robustness có kết quả JSON/CSV. Báo cáo phân biệt kết quả đo được, kết quả tham khảo từ source upstream và các thí nghiệm chưa thực hiện.

**Từ khóa:** Steganography, Steganalysis, CTF, pixel-difference encoding, Amplitude Shift Keying, FFT, STFT, cross-correlation.

## 1. Giới thiệu và thiết kế đồ án

### 1.1. Bối cảnh và mục tiêu

Steganography tập trung che giấu sự tồn tại của thông điệp trong một vật mang tin, chẳng hạn ảnh hoặc âm thanh. Khác với mật mã học, mục tiêu không chỉ là làm cho nội dung khó đọc mà còn làm cho người quan sát khó nhận ra có dữ liệu bổ sung. Người gửi cần nhúng thông điệp sao cho ít gây nghi ngờ; người phân tích cần nhận biết bất thường và khôi phục thông điệp khi có đủ bằng chứng.

Đồ án chọn hai challenge sử dụng hai loại vật mang tin khác nhau. Blue 3 thể hiện cách nhúng dữ liệu trong miền không gian của ảnh, còn Sleepy Alarm thể hiện cách nhúng trong miền tín hiệu của âm thanh. Cặp challenge này cho phép so sánh hai hướng phân tích: thống kê pixel theo vùng và phân tích tín hiệu theo tần số/thời gian.

Mục tiêu cụ thể:
1. Tái hiện hai challenge bằng artifact chính thức, giữ nguyên dữ liệu đầu vào và ghi SHA-256.
2. Tự xây dựng decoder thay vì chỉ sử dụng lời giải có sẵn.
3. Phân tích điều kiện toán học khiến decoder hoạt động và điều kiện khiến nó thất bại.
4. So sánh cách giải có thông tin từ source với cách giải dựa trên artifact.
5. Tạo thí nghiệm kiểm tra độ nhạy của kỹ thuật nhúng trước một số phép biến đổi.
6. Đánh giá dấu hiệu phát hiện và biện pháp phòng thủ đối với ảnh/âm thanh có dữ liệu ẩn.

### 1.2. Lý do lựa chọn và so sánh phương án

Assignment yêu cầu chọn một chủ đề CTF chính và khuyến nghị một cụm challenge nhất quán gồm hai challenge có liên hệ, hoặc một challenge khó kèm phần mở rộng có ý nghĩa [10]. Hai challenge được chọn đều thuộc hướng steganography, nhưng bổ sung cho nhau về dữ liệu và công cụ.

| Phương án | Cơ chế và giá trị nghiên cứu | Lý do chọn / không chọn |
|---|---|---|
| **Blue 3 — BYUCTF (chọn)** | Tổng sai khác RGB theo vùng chéo; tự suy luận và viết decoder | Có artifact, creator source và solver tham khảo; cho phép đối chiếu white-box/black-box |
| **Sleepy Alarm — ImaginaryCTF (chọn)** | ASK 8 kHz trong audio; phân tích phổ, đồng bộ và khôi phục symbol | Bổ sung miền tín hiệu khác với ảnh; có source tạo tín hiệu và track gốc để kiểm chứng |
| Bài ảnh LSB phổ thông (không chọn) | Đọc bit thấp của kênh màu; dễ tái hiện | Ít chiều sâu nếu chỉ chạy công cụ; cần phần mở rộng riêng |
| Steghide (không chọn) | Trích payload bằng công cụ đóng gói | Phụ thuộc passphrase/công cụ; khó so sánh thuật toán nếu thiếu source hoặc biến thể |

Blue 3 được ưu tiên vì source mô tả thuật toán cụ thể, ảnh đầu vào có sẵn và có thể tự kiểm tra từ dữ liệu. Sleepy Alarm bổ sung một bài toán tín hiệu khác hẳn, đồng thời tạo điều kiện phân tích sự khác nhau giữa dữ liệu gốc, tín hiệu đã trộn và tín hiệu sau nén MP3. Việc chọn hai bài không nhằm tăng số lượng flag mà nhằm tạo phép so sánh có cùng chủ đề nhưng khác miền biểu diễn.

### 1.3. Đối chiếu với các repository mã nguồn mở

Để xác định vị trí của đồ án trong hệ sinh thái công cụ hiện có, báo cáo khảo sát README và tài liệu công khai của ba repository liên quan. Đây là đối chiếu phạm vi/chức năng trên tài liệu, **không phải benchmark**: các repository bên ngoài không được cài đặt hoặc chạy trên cùng bộ dữ liệu trong đồ án này.

| Repository | Phạm vi được mô tả công khai | Hàm ý đối với STEGO |
|---|---|---|
| **Aperi'Solve** [11] | Nền tảng steganalysis ảnh; trực quan hóa bit-plane theo kênh R/G/B/Alpha và tích hợp zsteg, steghide, outguess, exiftool, binwalk, foremost, pngcheck, strings | Forensic ảnh thực tế cần nhiều detector độc lập; decoder Blue 3 chuyên biệt không thay thế pipeline đa công cụ |
| **The-A-Files** [12] | Framework đánh giá audio steganography/watermarking; README mô tả 30 phương pháp, 26 nhóm attack và 25 metric, tách payload recovery, chất lượng tín hiệu, robustness, capacity và detectability | Đánh giá robustness nên bao phủ nhiều phép biến đổi và metric, không chỉ exact-match |
| **ragibson/Steganography** [13] | Cài đặt LSB cho BMP/PNG, WAV và byte sequence; có LSB steganalysis đơn giản cho ảnh bitmap | Detector theo họ LSB không mặc nhiên giải được phép tổng sai khác RGB của Blue 3 hoặc ASK của Sleepy Alarm |

Đối chiếu này cho thấy đóng góp phù hợp của STEGO là nghiên cứu tái hiện có kiểm soát trên hai challenge: giải thích cơ chế, tự triển khai decoder, giữ lại lỗi trung gian và lưu bằng chứng có thể tái chạy. Khoảng trống so với các framework rộng hơn nằm ở số họ thuật toán, quy mô corpus, detector, metric chất lượng và độ đa dạng của attack. Không có cơ sở để tuyên bố STEGO vượt trội các dự án trên khi chưa có benchmark trực tiếp.

### 1.4. Câu hỏi nghiên cứu và giả thuyết

- **RQ1:** Tổng sai khác RGB theo từng vùng có đủ thông tin để khôi phục ký tự đã nhúng trong Blue 3 hay không?
- **RQ2:** Phân tích phổ và envelope có thể tách tín hiệu ASK 8 kHz khỏi âm thanh nền trong Sleepy Alarm hay không?
- **RQ3:** Kết quả giải mã thay đổi thế nào khi ảnh bị JPEG recompression/resize hoặc âm thanh bị resampling/gain/clipping?
- **RQ4:** Có thể xây dựng dấu hiệu phát hiện steganography từ đặc trưng pixel và phổ âm thanh không?

Các giả thuyết:
- **H1 — Blue 3:** Nếu màu nền được xác định đúng, ảnh còn nguyên vẹn và kích thước không thay đổi, tổng chênh lệch ba kênh RGB trong vùng ký tự thứ i bằng mã ASCII của ký tự đó.
- **H2 — Sleepy Alarm:** Nếu tách được thành phần quanh 8 kHz, giữ đúng đồng hồ symbol 50 baud và phân biệt được ba trạng thái biên độ, có thể phục hồi 350 symbol tương ứng 39 byte và 38 dấu phân cách.
- **H3 — Độ bền:** JPEG recompression/resize có thể phá hủy quan hệ pixel tuyệt đối của Blue 3; resampling, filtering hoặc clipping có thể làm sai biên độ/thời điểm symbol của Sleepy Alarm.

### 1.5. Tiêu chí xác nhận thành công

| Challenge | Điều kiện xác nhận | Kết quả đã đo |
|---|---|---|
| Blue 3 | Khôi phục flag, đối chiếu nguồn chính thức, ghi hash và thông số ảnh | Đạt: flag 50 ký tự; 49 độ dài ứng viên; PNG RGB 512 × 512 |
| Sleepy Alarm | 350 symbol, 38 separator, 39 byte; không byte lỗi; exact-match ground truth | Đạt: 39/39 ký tự; prefix/suffix hợp lệ; errors rỗng; ground_truth_match=true |
| Robustness | Chạy decoder trên biến thể và ghi tham số | Đạt trong phạm vi đã thử: 5 biến thể ảnh; 4/4 phép audio theo cặp target/reference PASS; thí nghiệm bất đối xứng có 3/6 phép thử PASS và 3/6 FAIL |

### 1.6. Liên hệ trực tiếp với rubric

| Tiêu chí | Điểm tối đa | Minh chứng chính |
|---|---:|---|
| Lập kế hoạch và biện minh | 2,0 | Mục 1: RQ/H1–H3, so sánh phương án, lý do chọn hai challenge cùng chủ đề |
| Triển khai và tài liệu hóa | 4,0 | Mục 3–8: artifact và SHA-256, lệnh, decoder, 22/22 test đã pass tại source commit được quality gate ghi nhận, hình và CSV/JSON đã lưu |
| Phân tích kết quả | 2,0 | Mục 2, 5, 6, 9, 10: chứng minh toán học, 350 symbol ASK, lỗi và điều kiện giải |
| Đánh giá, phản biện và tự học | 2,0 | Mục 11.1–11.9: hạn chế định lượng, threat model, validity, phản biện hai decoder, benchmark detector, ma trận khắc phục và kế hoạch học tiếp |

Bảng này là bản đồ đối chiếu với rubric, không phải tự chấm điểm. Điểm số chỉ do giảng viên quyết định dựa trên báo cáo và khả năng trình diễn lại.

## 2. Kiến thức nền và mô hình kỹ thuật

### 2.1. Mô hình steganography

Có thể mô tả quá trình nhúng tổng quát:

**Mô hình nhúng:** `S = E(C, M, K, θ)`. Trong đó `C` là vật mang tin, `M` là thông điệp, `K` là khóa (nếu có), `θ` là bộ tham số và `S` là vật mang tin sau khi nhúng.

Quá trình trích xuất tìm:

**Mô hình trích xuất:** `M_hat = D(S, K, θ)`. Decoder nhận vật mang tin đã nhúng và khôi phục thông điệp ước lượng.

Một kỹ thuật ẩn tin thường được đánh giá qua ba yếu tố: dung lượng (payload capacity), tính khó phát hiện (imperceptibility) và độ bền (robustness). Ba yếu tố này có thể xung đột. Ví dụ, thay đổi nhiều pixel có thể tăng dung lượng nhưng làm phân bố màu dễ bị phát hiện; nén ảnh có thể phá hủy payload.

### 2.2. Blue 3: mã hóa bằng tổng sai khác RGB

Theo README và creator script chính thức, ảnh được tạo từ nền đồng nhất RGB = (64, 77, 205), kích thước 512 × 512. Với flag có độ dài L, đặt:

**Kích thước cạnh vùng:** `s = floor(512 / L)`, với `L` là độ dài flag.

Ký tự thứ i được gắn với vùng vuông:

**Vùng của ký tự thứ i:** `R_i = [i·s, (i+1)·s) × [i·s, (i+1)·s)`.

Trong mỗi vòng lặp tương ứng một đơn vị mã ký tự, creator chọn ngẫu nhiên một pixel thuộc R_i và tăng một đơn vị ở một trong ba kênh RGB. Nếu pixel được chọn nhiều lần, các mức tăng được cộng dồn.

Gọi B=(64,77,205) là màu nền và I(x,y,c) là giá trị kênh c tại pixel (x,y). Tổng sai khác của vùng i:

**Tổng sai khác RGB của vùng i:** `Δ_i = Σ_(x,y)∈R_i Σ_(c∈{R,G,B}) (I(x,y,c) − B_c)`, trong đó `B=(64,77,205)` là màu nền.

Mỗi thao tác nhúng chỉ tăng đúng một đơn vị ở đúng một kênh. Do đó, nếu ảnh không bị biến đổi và không xảy ra tràn/clipping giá trị kênh:

**Quan hệ mã hóa:** `Δ_i = ord(m_i)`, vì mỗi đơn vị mã ký tự làm tăng đúng một đơn vị ở một kênh RGB trong vùng.

Suy ra ký tự:

**Khôi phục ký tự:** `m_hat_i = chr(Δ_i)`.

Phép tổng hợp không cần biết pixel nào đã bị thay đổi, kênh nào được chọn hay thứ tự ngẫu nhiên của creator. Các thao tác tăng một đơn vị có tính cộng, nên tổng sai khác giữ lại số lần tăng của cả vùng. Điều kiện thành công là xác định đúng L, đúng màu nền, đúng ranh giới vùng và bảo toàn giá trị pixel.

Với flag thực tế có 50 ký tự, s = floor(512/50) = 10. Mỗi ký tự tương ứng vùng 10 × 10 pixel; 50 vùng bao phủ 5.000 vị trí pixel trên đường chéo. Mép phải và mép dưới còn 12 pixel không thuộc các vùng được duyệt. Tổng số lần tăng kênh suy ra từ chuỗi flag chính thức là 5.164; số lần tăng có thể lớn hơn số vị trí pixel vì một pixel có thể được chọn lặp lại.

### 2.3. Sleepy Alarm: điều chế ASK trong miền thời gian

Source MATLAB của challenge mô tả ba trạng thái biên độ:
- 0: dấu phân cách/kết thúc một byte.
- 2 × 10⁻³: bit 0.
- 5 × 10⁻³: bit 1.

Sóng mang có tần số fc = 8.000 Hz. Tốc độ symbol Rs = 50 baud, nên thời lượng mỗi symbol Ts = 1/Rs = 0,02 giây. Với sample rate 44.100 Hz, số mẫu mỗi symbol là:

**Số mẫu trên mỗi symbol:** `N_s = f_s × T_s = 44,100 × 0.02 = 882 samples`.

Một ký tự ASCII gồm 8 bit. Flag dài 39 ký tự nên có 312 bit. Generator chèn một dấu phân cách giữa các byte, tạo 38 dấu phân cách. Tổng số symbol là:

**Tổng symbol:** `N_symbol = 39 × 8 + 38 = 350`, gồm 312 bit dữ liệu và 38 dấu phân cách.

350 symbol × 0,02 giây = 7 giây. Trong mỗi symbol, sóng mang có 8.000 × 0,02 = 160 chu kỳ. Generator MATLAB cộng tín hiệu ASK vào cột thứ nhất của ma trận audio, tức kênh trái trong file stereo. Vì vậy, lấy trung bình hai kênh trước khi giải mã sẽ làm suy giảm biên độ thành phần ASK.

### 2.4. FFT, STFT và envelope

Biến đổi Fourier rời rạc:

**DFT:** `X[k] = Σ_(n=0)^(N−1) x[n] · exp(−j·2π·k·n/N)`. Độ phân giải tần số là `Δf = f_s / N`. FFT trên toàn file phù hợp để xác định peak tần số nhưng không cho biết peak xuất hiện ở thời điểm nào. STFT chia tín hiệu thành các cửa sổ ngắn; spectrogram biểu diễn năng lượng theo thời gian và tần số. Sau khi lọc băng quanh sóng mang, analytic signal/Hilbert transform có thể dùng để lấy envelope, từ đó ước lượng mức biên độ trong phần giữa mỗi symbol.

Đối với Sleepy Alarm, các tham số quan trọng là tần số cắt bộ lọc, kích thước cửa sổ STFT, hop length, vị trí bắt đầu symbol và cách xử lý âm thanh nền. Spectrogram không phải bằng chứng duy nhất; kết luận phải phù hợp với số symbol, mức biên độ, cấu trúc byte và độ dài flag được challenge gợi ý.

## 3. Nguồn dữ liệu và tính toàn vẹn

Các artifact được lấy từ repository chính thức, tải về bằng script có kiểm tra kích thước và tính SHA-256 cục bộ.

- **Blue 3 — blue.png:** 9.406 bytes; SHA-256 `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e`.
- **Sleepy Alarm — morning_n_breakfast.mp3:** 179.283 bytes; SHA-256 `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2`.
- **Track tham chiếu — morning_n_breakfast_original.mp3:** 160.495 bytes; SHA-256 `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad2`.

Ba artifact chính thức được lưu nguyên bản trong data/; nguồn và commit upstream được liệt kê tại [1]–[5].

Blue 3 có định dạng PNG, mode RGB, kích thước 512 × 512, 262.144 pixel; Pillow không báo metadata key. Các giá trị kênh quan sát được:

| Kênh | Miền giá trị | Mean ± Std | Số giá trị |
|---|---:|---:|---:|
| R | 64–68 | 64,006634 ± 0,093454 | 5 |
| G | 77–81 | 77,006531 ± 0,094254 | 5 |
| B | 205–209 | 205,006535 ± 0,094233 | 5 |

Các giá trị min/max nhất quán với mô hình nền (64,77,205) được tăng từng đơn vị. Tuy nhiên, chỉ các thống kê này chưa đủ chứng minh payload; bằng chứng quyết định là tổng sai khác theo đúng phân vùng và kết quả giải mã đối chiếu với flag chính thức.

## 4. Môi trường thực nghiệm và công cụ

### 4.1. Cấu hình ghi nhận từ máy chạy

| Thành phần | Phiên bản/cấu hình |
|---|---|
| Hệ điều hành | macOS 15.7.4 |
| Kiến trúc | arm64 |
| Python | 3.14.10 |
| Pillow | 13.0.0 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |
| SoundFile | 0.14.0 |
| Quản lý môi trường | uv và virtual environment .venv |

Pillow đọc ảnh và trích ma trận RGB; NumPy tính tổng và thống kê mảng; SciPy thực hiện lọc, cross-correlation và STFT; SoundFile đọc dữ liệu audio; Matplotlib xuất histogram, waveform, spectrogram và envelope.

### 4.2. Cài đặt và tái lập

~~~bash
uv venv --python 3.14
source .venv/bin/activate
uv pip install -r requirements.txt
python scripts/check_environment.py
python scripts/download_artifacts.py all
python -m unittest discover -s tests -v
~~~

Không chỉnh sửa artifact gốc. Mọi ảnh JPEG, ảnh resize, audio resample hoặc audio gain/clipping phải được lưu trong thư mục kết quả riêng. Trước mỗi lần chạy, ghi lại hash input, lệnh, tham số và thời gian chạy.

## 5. Quy trình thực hiện và kết quả Blue 3

### 5.1. Khảo sát ban đầu

Lệnh chạy:

~~~bash
python src/blue3/analyze.py data/blue3/blue.png
~~~

Kết quả cho thấy PNG RGB 512 × 512, không có metadata key và các kênh chỉ sử dụng 5 mức giá trị nằm sát màu nền. Đây là chỉ dấu phù hợp với một phép biến đổi pixel có biên độ nhỏ. Giả thuyết được đặt ra là tổng độ lệch của từng vùng đường chéo có thể biểu diễn mã ký tự.

### 5.2. Decoder và tìm độ dài flag

Lệnh chạy:

~~~bash
python src/solve_challenges.py blue3 data/blue3/blue.png
~~~

Trong lần chạy đầu, decoder sử dụng màu nền RGB (64,77,205), thử các độ dài ứng viên và cộng tổng sai khác RGB của mỗi vùng. Kết quả terminal:

~~~text
Candidate: byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}
Attempts: 49
Format validated: True
~~~

Chuỗi có 50 ký tự và trùng chính xác với flag trong README chính thức của BYU-CSA [1]. Đây là xác minh độc lập ở mức kết quả: decoder khôi phục từ pixel, sau đó được so sánh với giá trị do ban tổ chức công bố. Việc khớp regex đơn thuần sẽ yếu hơn vì có thể xuất hiện ứng viên ngẫu nhiên; đối chiếu với flag chính thức làm giảm đáng kể khả năng kết luận nhầm.

### 5.3. Tự triển khai và so sánh hai cách xác định màu nền

Creator source công bố màu nền RGB (64,77,205). Tuy nhiên, để tránh phụ thuộc vào thông tin source khi giải hard-mode chỉ cung cấp ảnh, decoder mới có hai cách:
1. **Black-box:** suy luận màu nền là bộ RGB xuất hiện phổ biến nhất trong ảnh.
2. **Source-informed:** truyền trực tiếp màu nền biết từ creator source qua tham số.

Phiên bản hiện tại đặt black-box làm mặc định. Lần chạy black-box trên PNG chính thức đã khôi phục cùng flag sau 49 ứng viên; log được lưu tại `results/logs/blue3-solver.log`. Chế độ source-informed được giữ làm đối chứng để tách biệt lợi ích của thông tin creator với suy luận chỉ dựa trên artifact.

### 5.4. Độ phức tạp và điều kiện thành công

Với mỗi ứng viên L, tổng số pixel được xét trên L vùng xấp xỉ L × (512/L)² = 512²/L. Khi thử nhiều độ dài, tổng lượng công việc tăng theo O(n² log n) trong trường hợp tổng quát. Bộ nhớ chính để giữ ma trận ảnh là O(n²). Với ảnh 512 × 512, phép tính nhẹ và phù hợp máy cá nhân.

Các điều kiện cần:
- Dữ liệu ảnh còn nguyên giá trị pixel, không bị JPEG recompression hoặc resize.
- Kích thước và hình học vùng còn đúng 512 × 512.
- Màu nền được xác định chính xác.
- Creator chỉ tăng giá trị kênh; không có phép biến đổi làm đổi dấu/số lượng sai khác.
- Độ dài L được xác định đúng.

### 5.5. Hình phân tích ảnh

Hình 1 được tạo trực tiếp từ `blue.png` bằng script `src/blue3/visualize.py`. Ba panel lần lượt biểu diễn phân bố giá trị RGB, heatmap độ lệch lớn nhất giữa pixel và màu nền (64,77,205), và tổng sai khác RGB trong từng vùng chéo. Biểu đồ vùng là bằng chứng trực quan bổ sung cho decoder: nếu giả thuyết đúng, các tổng vùng phải tương ứng với mã ký tự và không cần xác định từng pixel bị thay đổi.

![Hình 1. Histogram RGB, bản đồ sai khác pixel và tổng sai khác theo vùng đường chéo của Blue 3. Nguồn: tự tạo từ artifact chính thức.](../results/blue3/figures/blue3_diagnostics.png)

Lệnh tái hiện:

~~~bash
python src/blue3/visualize.py data/blue3/blue.png --length 50 --out-dir results/blue3/figures
~~~

## 6. Quy trình và kết quả Sleepy Alarm

### 6.1. Khảo sát và xác định cơ chế

Challenge mô tả một jingle yếu trong file báo thức. Source README chỉ ra peak khác thường ở 8 kHz và ba mức biên độ sau khi cô lập sóng mang. Source MATLAB xác định payload 350 symbol, 50 baud, thời gian truyền 7 giây và việc cộng tín hiệu ASK vào kênh audio đầu tiên [4][5].

Các file MP3 được tải và xác minh SHA-256. Lần phân tích đầu tiên với reference báo lỗi do hai file sau giải mã không có cùng số frame. Module audio_alignment được bổ sung để chuyển đổi sample rate khi cần, ước lượng offset bằng cross-correlation và chỉ trừ phần hai tín hiệu chồng lấp.

### 6.2. Lần giải mã đầu tiên — kết quả thất bại được giữ lại

Lần chạy solver đầu tiên với reference ghi nhận:

| Thông số | Giá trị |
|---|---:|
| Sample rate | 44.100 Hz |
| Số kênh | 2 |
| Thời lượng phần overlap | 9,952653 s |
| Alignment lag | 1.729 samples |
| Alignment lag theo thời gian | 0,039206 s |
| Số frame overlap | 438.912 |
| Normalized absolute correlation | 0,9998734 |
| Symbol đã xử lý | 497 |
| Separator bị nhận diện | 161 |
| Unknown symbol | 0 |
| Khoảng envelope median | 0,0000312 đến 0,0030983 |
| Byte NUL thu được | 17 |
| Nhóm bit không đủ 8 bit | 18 |

Solver trả về chuỗi NUL và các nhóm bit có độ dài không hợp lệ. Đây là **kết quả thất bại**, không phải flag. Việc giữ lại lần thất bại có giá trị vì nó cho thấy độ tương quan cao giữa hai soundtrack không đồng nghĩa decoder đã lấy đúng payload. Cross-correlation chỉ hỗ trợ căn chỉnh nền âm thanh; nó không tự chứng minh biên symbol hoặc biên độ đã được nhận dạng đúng.

### 6.3. Phân tích nguyên nhân

Lần triển khai cũ mắc ba vấn đề kỹ thuật:
1. **Trung bình hai kênh stereo:** generator chỉ thêm ASK vào channel 0. Việc lấy trung bình hai kênh làm giảm thành phần ASK và thay đổi phân bố envelope.
2. **Xử lý cả file thay vì payload:** file dài gần 10 giây nhưng generator chỉ tạo chuỗi ASK 7 giây. Vì vậy, lần chạy cũ xử lý 497 symbol thay vì 350.
3. **Ngưỡng cố định chưa phù hợp:** ngưỡng 0,002 và 0,005 được mô tả trong source generator, nhưng tín hiệu đã qua MP3 encoding và bước lấy envelope. Dùng trực tiếp các ngưỡng này sau khi trộn/trừ audio có thể phân loại sai.

### 6.4. Phiên bản decoder đã điều chỉnh

Phiên bản hiện tại của solver và analyzer thực hiện quy trình:
1. Đọc hai MP3, resample reference nếu sample rate khác; ước lượng offset bằng cross-correlation và chỉ lấy phần overlap.
2. Giữ prefix của distributed MP3 trước điểm bắt đầu overlap rồi ghép với residual. Prefix này có thể chứa các symbol ASK đầu tiên; bỏ nó làm mất bit đầu.
3. Phân tích channel 0 (left), vì creator chỉ chèn ASK vào kênh thứ nhất.
4. Dùng coherent detection: chiếu từng cửa sổ 882 mẫu lên hai cơ sở sin/cos 8 kHz và tính biên độ I/Q. Mỗi symbol có 160 chu kỳ sóng mang; phép chiếu toàn symbol tránh transient ở đầu chuỗi của Hilbert-envelope sau lọc.
5. Phân cụm ba mức thấp/trung bình/cao thành separator/bit 0/bit 1; nhóm 8 bit thành byte.
6. Kiểm tra 350 symbol, 38 separator, 39 byte, độ dài 39 và đối chiếu toàn bộ chuỗi với ground truth được đọc độc lập từ bitmap creator.

Một lần chạy đầu tiên dùng Hilbert-envelope và xử lý cả file đã thất bại; log được giữ tại results/2026-11-14/initial-run.md. Sau khi sửa đúng kênh, cửa sổ payload, prefix alignment và phép đo biên độ, decoder mới đã exact-match trên MP3 phân phối.

Việc đối chiếu chính xác toàn bộ chuỗi là điều kiện bắt buộc để `success=true`. Chỉ khớp prefix/suffix không được xem là giải thành công.

### 6.5. Kết quả giải mã trên MP3 chính thức

Phiên bản coherent detector đã chạy trên file phân phối và so sánh với ground truth được đọc độc lập từ bitmap trong createsignal.m. Output đầy đủ được lưu trong results/sleepy_alarm/solver.json.

| Đại lượng | Kết quả |
|---|---:|
| Sample rate / kênh phân tích | 44.100 Hz / channel 0 (left) |
| Alignment lag | 1.729 mẫu = 0,039206 s |
| Normalized absolute correlation | 0,9998734 |
| Prefix được giữ trước overlap | 1.729 mẫu |
| Symbol đã giải | 350/350 |
| Separator / bit 0 / bit 1 | 38 / 153 / 159 |
| Tâm cụm biên độ | 0,0001035 / 0,0019975 / 0,0049727 |
| Byte giải mã / byte lỗi | 39 / 0 |
| Exact-match | PASS |

Tâm cụm bit 0 và bit 1 lệch lần lượt khoảng −0,13% và −0,55% so với mức danh định 0,002 và 0,005. Cụm separator ở khoảng 0,0001035 phản ánh nhiễu/codec còn lại sau phép trừ tham chiếu.

**Chuỗi trích xuất từ MP3:** ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}. Chuỗi 39 ký tự khớp toàn bộ bitmap ground truth của creator; errors=[]; format_valid=true; ground_truth_match=true. Ground truth chỉ được dùng sau trích xuất để xác minh chính xác, không làm đầu vào cho decoder.

### 6.6. Lệnh tái hiện

Các lệnh cài môi trường, phân tích, giải mã và xác minh Sleepy Alarm được tập trung tại **Phụ lục A** để tránh lặp lại command trong phần kết quả. Khi chạy, cần truyền đúng file target và file reference như mô tả; expected flag chỉ dùng để exact-match validation, không được dùng làm đầu vào trích xuất.

## 7. Công cụ tự viết và kiểm thử

| Thành phần | Chức năng và bằng chứng |
|---|---|
| src/solve_challenges.py | Hai decoder; stdout/JSON, thông số và exact-match |
| src/blue3/analyze.py, visualize.py | Metadata, RGB histogram, heatmap pixel và tổng delta theo vùng chéo |
| src/sleepy_alarm/analyze.py | Waveform, spectrogram, envelope và alignment metadata |
| src/audio_alignment.py | Resampling, cross-correlation và đoạn overlap |
| src/experiments/*_robustness.py | Ma trận biến đổi ảnh/audio và kết quả CSV/JSON |
| src/experiments/robustness_metrics.py | Character edit distance, normalized similarity, BER và separator precision/recall |
| scripts/verify_reproducibility.py | Quality gate: SHA-256, unit/integration tests, hai decoder chính thức và environment |
| tests/ | 22 test methods: hồi quy tổng hợp, integration trên artifact chính thức và kiểm thử metric |

`results/logs/unit-tests.log` là log lịch sử của 6 regression tests ở revision cũ. Bằng chứng hiện hành là `results/logs/quality-gate-tests.log`, ghi nhận 22/22 tests pass (exit code 0) trên source commit `11cd5e3216e779b6101b22cd891689ecdf9b8e54`. Commit `3015d5d` đưa log và JSON này cùng các kết quả robustness mới lên `main`; không có thay đổi source/tests giữa hai commit.

~~~bash
python scripts/verify_reproducibility.py
~~~

Quality gate hiện đã có bằng chứng chạy thành công: 22/22 tests, ba hash đúng, hai decoder exact-match trong điều kiện đã mô tả. `quality-gate.json` ghi source commit được kiểm thử; commit lưu bằng chứng sau đó có thể khác vì bản thân log/JSON chỉ được commit sau khi chạy. Khi thay đổi source, test hoặc artifact, phải chạy lại gate và lưu một kết quả mới.

## 8. Thiết kế thí nghiệm robustness

Mục tiêu là xác định mức độ nhạy của hai cơ chế nhúng trước các phép biến đổi phổ biến. Mọi phép biến đổi phải thực hiện trên bản sao; artifact gốc không bị ghi đè.

### 8.1. Blue 3

| Nhóm | Phép biến đổi | Tham số |
|---|---|---|
| Đối chứng | PNG gốc | Không biến đổi |
| Nén mất dữ liệu | JPEG recompression | Quality 95, 85, 70 |
| Thay đổi hình học | Resize | 0,75× và 0,5× |

Kết quả chạy trên GitHub Actions (Ubuntu 26.04, Python 3.14.10; runtime tính bằng giây trong một lượt CI):

| Biến thể | Kết quả decoder | Số ứng viên / runtime (s) |
|---|---|---:|
| PNG gốc | Khôi phục đúng flag | 49 / 0,237 |
| JPEG quality 95 | Không tìm thấy candidate | 511 / 0,575 |
| JPEG quality 85 | Không tìm thấy candidate | 511 / 0,569 |
| JPEG quality 70 | Không tìm thấy candidate | 511 / 0,565 |
| Resize 0,75× | Không tìm thấy candidate | 383 / 0,321 |
| Resize 0,5× | Không tìm thấy candidate | 255 / 0,134 |

CSV đầy đủ: `results/blue3/robustness/blue3_robustness.csv`. Ảnh tổng hợp chẩn đoán: `results/blue3/figures/blue3_diagnostics.png`.

Kết quả cho thấy **decoder cụ thể của Blue 3** không còn tìm được chuỗi flag sau các biến đổi JPEG/resize đã thử. Điều này phù hợp với cơ chế tổng sai khác pixel tuyệt đối và phân vùng dựa trên kích thước gốc: JPEG thay đổi giá trị kênh, còn resize thay đổi ranh giới vùng và số pixel trong mỗi vùng. Đây không phải kết luận rằng payload chắc chắn bị xóa khỏi ảnh hay mọi phương pháp steganography đều thất bại sau các phép biến đổi này; thí nghiệm chỉ đo khả năng giải bằng decoder đang nghiên cứu.

### 8.2. Sleepy Alarm — biến đổi đồng bộ target/reference

| Nhóm | Phép biến đổi | Tham số |
|---|---|---|
| Đối chứng | MP3 phân phối | Không biến đổi |
| Resampling | Round-trip | 44,1 kHz → 48 kHz → 44,1 kHz |
| Gain | Thay đổi amplitude | 0,5× và 1,5× có clipping |

Thí nghiệm được thực hiện sau khi baseline đã exact-match. Mỗi phép biến đổi được áp dụng đồng thời lên target và reference, sau đó chạy lại toàn bộ quy trình alignment và decoding. Kết quả:

| Biến thể | Exact-match | Separator | Clipping |
|---|---|---:|---:|
| MP3 gốc | PASS | 38 | 0% |
| Resampling round-trip 44,1→48→44,1 kHz | PASS | 38 | 0% |
| Gain 0,5× trên cả hai file | PASS | 38 | 0% |
| Gain 1,5× trên cả hai file | PASS | 38 | ~0,44% |

Tâm cụm biên độ sau resampling là 0,0001038 / 0,0019980 / 0,0049741; sau gain 0,5× là 0,0000517 / 0,0009987 / 0,0024864; sau gain 1,5× là 0,0001544 / 0,0029818 / 0,0074037. Với gain 1,5×, clipped-sample fraction được đo là 0,441% ở target và 0,442% ở reference, nhưng decoder vẫn khôi phục đúng 39 ký tự.

**Diễn giải:** decoder còn phục hồi được payload khi cùng một phép resampling/gain được áp dụng lên cả distributed track và reference. Kết quả không chứng minh khả năng chịu được biến đổi bất đối xứng (chỉ sửa target hoặc chỉ sửa reference), và không thể khái quát cho codec hoặc bộ lọc khác. Kết quả chi tiết được lưu trong results/sleepy_alarm/robustness/sleepy_alarm_robustness.csv.

Lệnh tái hiện:

### 8.3. Thí nghiệm bất đối xứng — phạm vi bổ sung

Để kiểm tra giới hạn trên, script `src/experiments/sleepy_alarm_asymmetric_robustness.py` áp dụng biến đổi lên đúng một phía của cặp target/reference. Baseline PASS với 350 symbol, 38 separator và exact-match 39 ký tự. Kết quả sáu phép thử:

| Biến thể | Exact-match | Số separator | Clipping phía bị đổi |
|---|---|---:|---:|
| Target-only gain 0,5× | **FAIL** | 46 | 0% |
| Target-only gain 1,5× | **FAIL** | 37 | 0,441% |
| Target-only resampling 44,1→48→44,1 kHz | **PASS** | 38 | 0% |
| Reference-only gain 0,5× | **FAIL** | 41 | 0% |
| Reference-only gain 1,5× | **FAIL** | 38 | 0,442% |
| Reference-only resampling 44,1→48→44,1 kHz | **PASS** | 38 | 0% |

Tổng cộng 3/6 phép thử PASS. Cả bốn trường hợp gain một phía đều FAIL; hai trường hợp resampling một phía đều PASS. Ở các trường hợp gain thất bại, decoder vẫn đo đủ 350 symbol nhưng phân loại sai số separator/bit, tạo các nhóm bit không đủ 8 bit và không khôi phục đúng ground truth. Đáng chú ý, alignment correlation vẫn nằm khoảng 0,99888–0,99987, cho thấy correlation cao không đảm bảo residual có biên độ phù hợp để giải mã ASK. Kết quả chỉ mô tả decoder và các phép biến đổi cụ thể này, không đại diện cho mọi mức gain hoặc codec.

Kết quả chi tiết nằm tại `results/sleepy_alarm/asymmetric_robustness/asymmetric_robustness.json` và `.csv`. Lệnh tái hiện:

### 8.4. Benchmark steganalysis và so sánh giải mã không reference

Benchmark seed 20261114 gồm các biến thể positive từ hai artifact chính thức và benign controls tổng hợp (12 ảnh, 8 audio). Các biến thể không phải mẫu độc lập thu thập từ thực tế.

| Modality | TP | TN | FP | FN | Precision | Recall | F1 | FPR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Image | 5 | 12 | 0 | 0 | 1,00 | 1,00 | 1,00 | 0,00 |
| Audio | 0 | 8 | 0 | 5 | 0,00 | 0,00 | 0,00 | 0,00 |

Điểm ảnh hoàn hảo không được diễn giải thành độ chính xác 100% trên ảnh nói chung: positive được tạo từ cùng một challenge và benign là dữ liệu tổng hợp. Ngược lại, detector audio **không phát hiện được bất kỳ positive nào** (FN=5, recall=0). Hai đặc trưng carrier-band energy và block-RMS CV cùng ngưỡng hiện tại chưa đủ phân biệt mẫu Sleepy Alarm. FPR=0 trên tám benign audio cũng không chứng minh detector không báo động nhầm trong thực tế.

| Chế độ Sleepy Alarm | Reference | Symbol | Separator | Độ dài | Format hợp lệ | Exact-match |
|---|---|---:|---:|---:|---|---|
| Reference-free | Không | 350 | 49 | 26 | Không | FAIL |
| Reference-assisted | Có | 350 | 38 | 39 | Có | PASS |

Không có reference, chuỗi giải mã chỉ dài 26 ký tự và có nhiều nhóm bit không đủ 8 bit; không thể xem là khôi phục payload. Khi có reference, residual cho phép khôi phục 39/39 ký tự. Đây vừa là bằng chứng lợi ích của reference trong challenge này, vừa là giới hạn nếu người phân tích không có bản nhạc gốc.

### 8.5. Robustness mở rộng

**Blue 3 — 9 phép biến đổi:** chỉ Gaussian blur radius 0,3 PASS; brightness 0,9/1,1, contrast 0,9/1,1, crop 16 px và Gaussian noise sigma 0,5/1,0/2,0 đều FAIL. Tỷ lệ thành công 1/9 (11,1%) trong các cấu hình cụ thể. Kết quả phù hợp với sự phụ thuộc của decoder vào pixel sum và hình học vùng; không thể suy ra mọi mức blur đều không ảnh hưởng.

**Sleepy Alarm — ma trận 23 trial:** kết quả lịch sử có 7/23 PASS (30,4%), bao gồm baseline. Các phép thử gồm gain một phía, AWGN ở nhiều SNR, band-pass và resampling. Đây là tỷ lệ trên một artifact và tập tham số định trước, không phải xác suất thành công trên mọi bản ghi audio.

**Đo partial recovery đã chạy và được lưu trong JSON/CSV:** Blue 3 ghi candidate ở độ dài baseline, số ký tự đúng theo vị trí, Levenshtein edit distance và normalized edit similarity. Sleepy Alarm ghi BER, symbol error rate và separator precision/recall cho từng trial. Ground truth chỉ được dùng sau extraction để chấm output, không làm đầu vào decoder. Các kết quả định lượng mới được phân tích tại mục 11.7.6.

Output nguồn: `results/steganalysis/benchmark.json`, `results/steganalysis/reference_comparison.json`, `results/blue3/extended_robustness/extended_robustness.json` và `results/sleepy_alarm/robustness_matrix/robustness_matrix.json`.

## 9. Phân tích an ninh: góc nhìn tấn công và phòng thủ

### 9.1. Góc nhìn tấn công

Blue 3 sử dụng phép biến đổi rất nhỏ trên các thành phần RGB, vì vậy ảnh nhìn tổng thể vẫn có màu xanh gần như đồng nhất. Thông tin được phân bố theo vùng đường chéo; không cần một pixel riêng biệt tương ứng một bit. Người giải phải xác định cấu trúc vùng và độ dài flag trước khi cộng sai khác.

Sleepy Alarm sử dụng sóng mang 8 kHz. Dữ liệu được biểu diễn bằng biên độ, không phải bằng sự hiện diện/vắng mặt của sóng mang. Người phân tích cần phát hiện peak, tách thành phần tín hiệu và khôi phục thời điểm symbol. Khi file đã được nén MP3, envelope có thể không còn đúng tuyệt đối mức 0,002 và 0,005 như trong source generator.

### 9.2. Dấu hiệu phát hiện

**Đối với ảnh:**
- Màu nền hoặc một màu chiếm ưu thế rất lớn.
- Phân bố giá trị kênh chỉ tập trung quanh một mức hẹp.
- Tổng sai khác trong các vùng đường chéo có thể cho ra chuỗi ký tự có cấu trúc.
- Phần sai khác ảnh tập trung có quy luật không gian.

**Đối với âm thanh:**
- Peak phổ bất thường ở quanh 8 kHz.
- Envelope có ba mức phân bố và lặp theo chu kỳ 0,02 giây.
- Sau khi so sánh với bản tham chiếu, residual có thành phần hẹp băng quanh sóng mang.
- Các symbol có thể nhóm thành byte 8 bit, ngăn cách bởi mức biên độ thấp.

Các dấu hiệu trên chỉ là heuristic. Một ảnh đồ họa có màu nền đơn giản hoặc một âm thanh có thành phần cao tần không mặc nhiên là steganography. Muốn giảm false positive, cần kết hợp nhiều dấu hiệu và kiểm tra tính nhất quán của cấu trúc thông điệp.

### 9.3. Biện pháp phòng thủ

- Quản lý nguồn gốc file, hash và bản gốc để phục vụ so sánh.
- Kiểm tra metadata, định dạng thật và sự nhất quán giữa phần mở rộng với cấu trúc file.
- Với ảnh, dùng phân tích histogram, màu nền, phân bố vùng và mô hình steganalysis phù hợp; không chỉ dựa trên quan sát bằng mắt.
- Với âm thanh, kiểm tra phổ, STFT, envelope, kênh stereo và các mẫu lặp bất thường.
- Giữ bản gốc trước mọi bước normalize, resize, recompress hoặc resample.
- Cảnh báo steganalysis nên được xem là tín hiệu điều tra tiếp, không tự động kết luận file độc hại.

## 10. So sánh kết quả hai challenge

| Khía cạnh | Blue 3 | Sleepy Alarm |
|---|---|---|
| Vật mang tin | PNG 512 × 512 RGB | MP3 stereo |
| Miền biểu diễn | Không gian/pixel | Thời gian/tần số |
| Cơ chế | Tổng sai khác RGB theo vùng | ASK ba mức biên độ |
| Thông tin cần suy luận | Độ dài L, màu nền, ranh giới vùng | Carrier, baud, symbol clock, channel, biên độ |
| Phép phân tích chính | Histogram, pixel sum | FFT/STFT, coherent I/Q projection |
| Ảnh hưởng của biến đổi | JPEG/resize thay đổi pixel và vùng | MP3/resampling ảnh hưởng biên độ và thời điểm |
| Kết quả thực nghiệm | Flag 50 ký tự khớp nguồn chính thức | Baseline exact-match; 4/4 phép biến đổi theo cặp PASS; 3/6 phép bất đối xứng PASS |

Blue 3 có cơ chế xác định và ổn định hơn vì PNG bảo toàn giá trị pixel; tổng sai khác có quan hệ trực tiếp với mã ký tự. Sleepy Alarm khó hơn ở khâu tách tín hiệu vì dữ liệu nằm trên âm thanh nền và file đã qua mã hóa MP3. Hai challenge cho thấy “đọc được dữ liệu ẩn” phụ thuộc không chỉ vào thuật toán nhúng mà còn vào loại vật mang tin và chuỗi xử lý file.

## 11. Đánh giá, hạn chế và quá trình tự học

### 11.1. Điểm mạnh

- Cặp challenge giữ chung một chủ đề CTF chính nhưng có hai miền dữ liệu khác nhau.
- Blue 3 và Sleepy Alarm đều đã được tái hiện trên artifact chính thức và exact-match với giá trị do ban tổ chức công bố.
- Decoder được tự triển khai; có chế độ suy luận màu nền và chế độ biết màu nền từ source để so sánh.
- Các lần giải mã Sleepy Alarm thất bại ban đầu được giữ lại để giải thích vì sao correlation cao chưa đủ; phiên bản cuối exact-match trên MP3 thật.
- Repository có script kiểm thử, công cụ trực quan hóa và kịch bản robustness.

### 11.2. Hạn chế hiện tại — kết quả định lượng

1. **Detector ảnh có dấu hiệu overfit theo challenge.** Benchmark cho ảnh đạt TP=5, TN=12, FP=0, FN=0, nhưng năm positive là các biến thể từ cùng một ảnh Blue 3 và benign controls là ảnh tổng hợp. Kết quả chỉ xác nhận heuristic nhận ra cấu trúc mẫu Blue 3, chưa chứng minh khả năng tổng quát hóa.
2. **Detector audio hiện không đạt mục tiêu.** Benchmark ghi TP=0, TN=8, FP=0, FN=5, tức recall=0 và F1=0. Toàn bộ positive audio bị bỏ sót. FPR=0 trên tám benign controls quá ít để kết luận detector không báo động nhầm trong thực tế.
3. **Giải mã Sleepy Alarm phụ thuộc reference.** Không có reference, solver xử lý 350 symbol nhưng tạo 49 separator, chỉ giải được 26 ký tự, format không hợp lệ và exact-match thất bại. Có reference, solver đạt 350 symbol, 38 separator và 39/39 ký tự. Thành công hiện tại là reference-assisted, không phải blind decoding.
4. **Robustness Blue 3 thấp trong ma trận mở rộng.** Chỉ 1/9 biến thể exact-match (Gaussian blur radius 0,3). Trong tám biến thể FAIL, sáu vẫn tạo candidate 50 ký tự để đo partial recovery: brightness 0,9 có 47/50 vị trí đúng, edit distance 3, similarity 94%; brightness 1,1 có 28/50 vị trí đúng, edit distance 20, similarity 60%; contrast 0,9 có edit distance 48, similarity 4%; contrast 1,1, crop 16 px và Gaussian noise sigma 2,0 có edit distance 50. Gaussian noise sigma 0,5 và 1,0 không tạo candidate ở độ dài baseline, nên edit distance được để null. Đây là khác biệt giữa exact-match thất bại và không còn candidate để đánh giá.
5. **Audio nhạy với điều kiện biến đổi.** Ma trận mở rộng có 7/23 PASS (bao gồm baseline). Trung bình số học trên 23 trial, bao gồm baseline, là SER 12,31%, BER 12,97%, separator precision 77,07% và recall 93,14%. Ví dụ target-side AWGN ở SNR 20 dB có SER 20,57% và BER 22,76%; reference-side AWGN ở 10 dB có SER 60,00% và BER 63,78%. Bốn phép gain một phía trong ma trận asymmetric ban đầu đều FAIL, trong khi hai phép resampling một phía PASS. Các giá trị trung bình này chỉ mô tả tập trial đã định trước, không phải ước lượng hiệu năng trên một quần thể audio.
6. **Quy mô mẫu hạn chế.** Nghiên cứu chỉ có hai challenge chính thức; các biến thể sinh từ một artifact không độc lập thống kê. Chưa có khoảng tin cậy, repeated runs trên nhiều payload hoặc kiểm định chéo theo challenge.
7. **Bằng chứng kiểm thử đã được đồng bộ ở mức source/evidence.** Quality gate ghi nhận 22/22 tests pass, exit code 0, trên source commit `11cd5e3216e779b6101b22cd891689ecdf9b8e54`; log và JSON đã được lưu trong commit `3015d5d`. `results/logs/unit-tests.log` vẫn chỉ là log lịch sử 6 test và không được dùng thay cho quality-gate log. Nếu source hoặc tests thay đổi sau revision được kiểm thử, cần chạy lại gate.
8. **Chưa có benchmark trực tiếp với công cụ ngoài.** Phần đối chiếu Aperi'Solve, The-A-Files và ragibson/Steganography dựa trên README/tài liệu công khai; không cài đặt, không chạy cùng corpus, không đo thời gian hoặc metric.

### 11.3. Phản biện kết quả và đánh giá tính hợp lệ

Các câu hỏi phản biện trọng yếu được phân tích theo threat model và validity ở mục 11.7. Trọng tâm là không đồng nhất exact-match với khả năng tổng quát, không dùng benchmark ảnh nhỏ để tuyên bố detector đạt 100%, không che giấu recall=0 của detector audio, và không gọi Sleepy Alarm là blind decoding khi kết quả hiện tại cần reference. Các kết quả robustness cũng chỉ có ý nghĩa trong đúng phép biến đổi và tham số đã chạy.

### 11.4. Hướng cải tiến và tiêu chí nghiệm thu

| Ưu tiên | Việc cần làm | Tiêu chí nghiệm thu |
|---|---|---|
| P0 — hoàn tất | Quality gate | 22/22 tests pass; ba artifact đúng hash; Blue 3 và Sleepy Alarm (có reference) exact-match; JSON/log đã commit |
| P1 | Phân tích feature và hiệu chuẩn detector audio trên validation độc lập | Recall/F1 báo cáo trên held-out test; không chọn ngưỡng từ test |
| P1 | Mở rộng corpus benign/stego nhiều nguồn | Split theo artifact/challenge, không để biến thể cùng nguồn rơi vào nhiều tập |
| P2 | Cải thiện reference-free Sleepy Alarm | Báo BER, byte exact-match và tỷ lệ payload phục hồi trên nhiều bản ghi |
| P2 | Mở rộng robustness theo cường độ | Có đường cong BER/exact-match theo gain, SNR, clipping, codec, crop và resampling |
| P3 | Benchmark công cụ ngoài trên cùng corpus | Cố định phiên bản, môi trường, tham số, thời gian và metric |

Không điều chỉnh ngưỡng chỉ để biến năm positive hiện tại thành PASS rồi báo cáo như kết quả độc lập. Nếu thay feature hoặc threshold, cần validation riêng và giữ test set chưa sử dụng để tránh overfitting.

### 11.5. Nhật ký và bằng chứng

Bằng chứng kỹ thuật có thể tái kiểm tra được lưu theo từng lớp: artifact và SHA-256 trong `data/` và `results/artifact_manifest.json`; log quality gate 22/22 tests trong `results/logs/quality-gate-tests.log`; báo cáo gate tại `results/verification/quality-gate.json`; kết quả Blue 3 trong `results/blue3/`; kết quả audio exact-match trong `results/sleepy_alarm/solver.json`; các ma trận robustness trong CSV/JSON; và lần giải mã Sleepy Alarm thất bại ban đầu trong `results/2026-11-14/initial-run.md`. Log sáu test cũ chỉ giữ vai trò lịch sử. `quality-gate.json` xác định source commit được kiểm tra; commit `3015d5d` là commit lưu bằng chứng sau khi chạy.

### 11.6. Tự đánh giá quá trình học tập và bài học rút ra

Hai challenge cho thấy giải steganography đòi hỏi kiểm chứng giả định, không chỉ tìm flag. Blue 3 cần suy luận quy luật biến đổi pixel và phân vùng; Sleepy Alarm cần xử lý stereo, đồng bộ thời gian và giải điều chế ASK.

Bài học rõ nhất đến từ việc giả thuyết ban đầu về alignment không đủ để giải thích kết quả. Lần chạy đầu xử lý 497 symbol thay vì 350, phân loại 161 separator và tạo nhiều byte lỗi. Correlation cao giữa hai MP3 chỉ cho thấy có thể căn chỉnh hai track; nó không chứng minh đã chọn đúng kênh, đúng đoạn payload hoặc đúng ba mức biên độ ASK. Phân tích lại source creator làm rõ ba điều kiện: ASK chỉ nằm ở channel 0, payload kéo dài 7 giây và chỉ có 350 symbol, còn phần prefix của distributed stream trước overlap có thể chứa các symbol đầu.

Từ các điều kiện đó, decoder được điều chỉnh theo từng giả định: không downmix hai kênh; giữ prefix 1.729 mẫu bị loại khỏi overlap; chỉ xử lý 7 giây; dùng cửa sổ 882 mẫu tương ứng 50 baud; và chiếu coherent lên hai cơ sở sin/cos ở carrier 8 kHz để ước lượng biên độ I/Q. Kết quả mới đạt 350 symbol, 38 separator, 39 byte và exact-match. Khi thử gain chỉ ở một phía, một số trường hợp vẫn có alignment correlation gần 1 nhưng giải mã sai. Điều này tiếp tục bác bỏ cách hiểu đơn giản rằng correlation cao đồng nghĩa residual có scale phù hợp.

Một thay đổi khác trong cách đánh giá là không xem PASS/FAIL như chỉ số duy nhất. Ma trận Blue 3 cho thấy brightness 0,9 vẫn giữ đúng 47/50 ký tự dù exact-match thất bại; ma trận audio cho thấy lỗi bit và lỗi separator cần được đo riêng. Vì vậy repository bổ sung edit distance, BER, SER và separator precision/recall, đồng thời giữ candidate thiếu ở trạng thái unavailable/null thay vì tự gán khoảng cách 0. Ground truth được sử dụng sau extraction để chấm output, không dùng làm đầu vào decoder.

Quy trình học rút ra là: đọc creator source để lập giả thuyết; kiểm tra giả thuyết bằng số đo trung gian; sửa từng điều kiện một; lưu nguyên bản artifact và hash; chạy lại trên artifact chính thức; và báo cáo cả kết quả thất bại lẫn thành công. Các bước phát triển kỹ thuật và số đo ở trên được hỗ trợ bởi source, log và JSON trong repository. Phần trải nghiệm chủ quan riêng của người thực hiện cần được xác nhận bằng lời của chính người đó, không thể suy ra từ commit.

### 11.7. Phản biện sâu: threat model, validity và diễn giải kết quả

#### 11.7.1. Threat model

| Vai trò | Mục tiêu | Giả định |
|---|---|---|
| Người nhúng | Che giấu payload trong cover | Biết thuật toán nhúng |
| Người phân tích có tri thức challenge | Khôi phục payload | Có mô tả/source; với Sleepy Alarm có thể có reference |
| Người phân tích mù | Phát hiện/khôi phục file chưa biết | Không mặc nhiên có source, khóa hoặc reference |

Blue 3 được giải với hiểu biết về creator algorithm; Sleepy Alarm là **reference-assisted** vì cần track gốc để tạo residual. Do đó đồ án chứng minh khả năng tái hiện challenge có điều kiện, chưa chứng minh blind steganalysis.

#### 11.7.2. Validity

| Loại | Hạn chế | Ảnh hưởng |
|---|---|---|
| Construct | Exact-match không đo chất lượng cover, dung lượng hay detectability | Khôi phục đúng không đồng nghĩa khó phát hiện |
| Internal | Target/reference có thể khác scale, encoder và xử lý | Lỗi có thể do pipeline residual/alignment |
| External | Hai challenge; biến thể positive cùng nguồn | Không khái quát sang ảnh tự nhiên, nhạc hoặc codec khác |
| Conclusion | Mẫu nhỏ, threshold thủ công, chưa có kiểm định độc lập | Chưa thể kết luận hiệu năng tổng quát |

#### 11.7.3. Phản biện Blue 3

Tổng sai khác RGB hoạt động vì các lần tăng một đơn vị được cộng dồn, không phụ thuộc pixel cụ thể đã chọn, nếu màu nền, kích thước ảnh và vùng R_i đều đúng. Nhưng decoder phụ thuộc màu nền, độ dài L và hình học vùng. Sai màu nền có thể tạo sai số tăng theo diện tích s²; resize/crop làm lệch ranh giới, còn JPEG thay đổi giá trị pixel. Kết quả chỉ cho thấy decoder hiện tại thất bại, không chứng minh payload đã bị xóa.

Việc thử 49 độ dài rồi chọn chuỗi theo định dạng flag là tìm kiếm tham số phù hợp với challenge có format biết trước, không phải suy luận độ dài phổ quát. Ảnh gần đơn sắc cũng có thể dễ bị phát hiện; khả năng giải mã cao không đồng nghĩa tính tàng hình cao.

#### 11.7.4. Phản biện Sleepy Alarm

Reference là dependency thiết yếu: reference-free chỉ khôi phục 26 ký tự, có 49 separator thay vì 38 và không đạt exact-match; reference-assisted khôi phục đủ 39 ký tự. Vì vậy không gọi decoder hiện tại là blind.

Correlation xấp xỉ 0,999 chủ yếu giúp xác định độ trễ/tương đồng, không bảo đảm hai track cùng scale. Gain một phía làm phần nền sau phép trừ không triệt tiêu tương ứng, khiến ba cụm ASK có thể chồng lấn hoặc lệch. Coherent I/Q projection còn giả định biết carrier 8 kHz, sample rate, pha và symbol timing 882 mẫu; sai lệch clock/pha có thể giảm năng lượng chiếu. Chọn kênh trái là đúng với generator của challenge nhưng không phải giả định tổng quát cho mọi file stereo.

#### 11.7.5. Phản biện detector

Benchmark có 17 ảnh (TP=5, TN=12, FP=0, FN=0) và 13 audio (TP=0, TN=8, FP=0, FN=5). Năm positive của mỗi modality đều xuất phát từ một artifact; benign controls là dữ liệu tổng hợp. Vì vậy image F1=1 chỉ cho thấy heuristic nhận diện họ mẫu Blue 3, không chứng minh generalization.

Với audio, carrier-band energy ratio của positive khoảng 0,000204, thấp hơn ngưỡng 0,02; block-RMS CV khoảng 0,987 nhưng detector yêu cầu đồng thời cả hai điều kiện nên bỏ sót toàn bộ positive. Đây là bằng chứng heuristic hiện tại không phù hợp với mẫu Sleepy Alarm trong benchmark, không phải lý do để hạ threshold ngay trên cùng tập dữ liệu. Cần validation độc lập, giữ test set riêng và báo confusion matrix/precision/recall/F1/FPR. FPR=0 trên tám mẫu audio tổng hợp không chứng minh không có false positive thực tế.

#### 11.7.6. Diễn giải robustness và kết luận

Không gộp các nhóm thử nghiệm khác điều kiện. Audio paired robustness áp dụng cùng biến đổi lên target/reference và đạt 4/4; asymmetric biến đổi một phía và đạt 3/6; ma trận mở rộng có 23 trial và đạt 7/23 (đều tính baseline). Blue 3 extended có 9 phép biến đổi và 1/9 exact-match. Ở sáu trường hợp thất bại nhưng có candidate độ dài 50, edit distance lần lượt là 3, 20, 48, 50, 50 và 50; hai mức Gaussian noise sigma 0,5 và 1,0 không có candidate ở độ dài baseline nên không có edit distance đo được. Ví dụ partial recovery cho thấy brightness 0,9 vẫn giữ đúng 47/50 ký tự, trong khi brightness 1,1 giữ 28/50. Với audio, mean SER 12,31%, mean BER 12,97%, mean separator precision 77,07% và recall 93,14% là trung bình không trọng số của 23 trial, có tính cả baseline. Một số trial minh họa: target AWGN 20 dB SER=20,57%/BER=22,76%; target AWGN 10 dB SER=55,14%/BER=57,37%; reference AWGN 20 dB SER=27,43%/BER=30,77%; reference AWGN 10 dB SER=60,00%/BER=63,78%. Các con số mô tả decoder và tham số cụ thể, không phải xác suất thành công phổ quát.

Kết luận được dữ liệu hỗ trợ là: hai decoder khôi phục đúng payload challenge trong điều kiện cụ thể; Blue 3 nhạy với biến đổi pixel; Sleepy Alarm cần reference và nhạy với gain bất đối xứng; detector audio chưa phát hiện positive trong benchmark. Không có bằng chứng để tuyên bố detector tổng quát, decoder audio blind hoặc robustness cao trong môi trường thực tế.

### 11.8. Ma trận hạn chế — tác động — hành động khắc phục

| Hạn chế | Mức ảnh hưởng | Hành động và bằng chứng cần có |
|---|---|---|
| Audio detector recall=0 | Rất cao | Phân tích feature; validation/test đa nguồn; confusion matrix và threshold |
| Sleepy Alarm cần reference | Cao | Phát triển blind synchronization; so sánh nhiều audio |
| Blue 3 nhạy JPEG/resize/noise | Cao | Báo BER/partial recovery theo cường độ biến đổi |
| Dataset nhỏ, positive cùng nguồn | Rất cao | Corpus độc lập; split theo artifact/challenge |
| Threshold đặt thủ công | Cao | Chọn threshold trên validation, không trên test |
| Thiếu metric cover | Trung bình | PSNR/SSIM cho ảnh, metric audio phù hợp khi có cover |
| Evidence regression | Thấp sau khi có gate | Giữ log sáu test ở vai trò lịch sử; nếu sửa source/tests thì chạy lại quality gate và lưu source commit được kiểm thử |
| Chưa benchmark tool ngoài | Trung bình | Cố định tool/version/corpus và so sánh metric |

### 11.9. Kế hoạch thực nghiệm tiếp theo và điều kiện dừng

| Ưu tiên | Thí nghiệm | Biến/chỉ số | Điều kiện nghiệm thu |
|---|---|---|---|
| P0 — hoàn tất | Xác nhận baseline | Commit source, 22 tests, exact-match, hash | Đã có quality-gate JSON/log; source commit được ghi rõ |
| P1 | Audio detector đa nguồn | Carrier, gain, SNR, codec; precision/recall/F1/FPR | Test độc lập, không tuning trên test |
| P2 | Image robustness sweep | JPEG, crop, noise, resize; BER/recovery | Có đường cong theo cường độ |
| P2 | Reference-free audio | Carrier offset, phase, baud, stereo; BER/exact-match | So sánh cùng corpus với reference-assisted |
| P3 | Generalization | Challenge/cover chưa dùng; metric theo modality | Không rò rỉ nguồn giữa các tập |

P0 (quality gate) và lần chạy P1 (partial-recovery metrics) đã hoàn tất. Các bước tiếp theo là nghiên cứu detector audio trên corpus độc lập, phát triển reference-free synchronization cho Sleepy Alarm và mở rộng robustness theo cường độ. Đây là công việc nghiên cứu mới, không phải điều kiện còn thiếu để xác nhận các kết quả đã có. Ưu tiên tính hợp lệ của tập test độc lập; không điều chỉnh threshold trên test set và luôn báo cả partial recovery lẫn exact-match.

## 12. Kết luận

Đồ án tái hiện hai challenge Steganography trên hai miền dữ liệu. Blue 3 được giải bằng tổng sai khác RGB theo vùng; Sleepy Alarm được giải bằng ASK 8 kHz/50 baud sau khi căn chỉnh và trừ reference. Cả hai payload khớp ground truth trong các điều kiện đã nêu.

Robustness khác nhau theo phép biến đổi: Blue 3 đạt 1/9 biến thể mở rộng; Sleepy Alarm đạt 4/4 phép biến đổi paired, 3/6 phép asymmetric và 7/23 trial ở ma trận mở rộng. Detector audio có recall=0 trên benchmark hiện tại; reference-free Sleepy Alarm thất bại. Các kết quả này giới hạn phạm vi kết luận: decoder làm việc trên challenge cụ thể, không chứng minh phát hiện tổng quát hay blind decoding.

Giá trị đồ án nằm ở decoder tự triển khai, phân tích giả định, giữ lại lỗi trung gian, đối chiếu ground truth và lượng hóa giới hạn. Revision được kiểm chứng hiện có 22/22 tests pass, các artifact đúng hash và cả hai decoder exact-match trong điều kiện đã nêu. Bộ partial-recovery metrics đã được chạy và lưu. Hướng nghiên cứu tiếp theo là mở rộng corpus độc lập cho detector, cải thiện reference-free audio và khảo sát robustness trên nhiều mức cường độ/nguồn dữ liệu.

## Tài liệu tham khảo

[1] BYU-CSA, “Blue 3? — BYUCTF Forensics/Steganography,” README và flag chính thức, repository old-ctf-challenges, commit 18c8f246756e79069c1cb1753c8bfea5e73e31f5. https://github.com/BYU-CSA/old-ctf-challenges/tree/master/forensics-steganography/blue-3

[2] BYU-CSA, “Blue 3 creator script,” create.py, cùng commit 18c8f246756e79069c1cb1753c8bfea5e73e31f5. https://github.com/BYU-CSA/old-ctf-challenges/blob/master/forensics-steganography/blue-3/create.py

[3] BYU-CSA, “Blue 3 reference solver,” solve.py, cùng commit 18c8f246756e79069c1cb1753c8bfea5e73e31f5. https://github.com/BYU-CSA/old-ctf-challenges/blob/master/forensics-steganography/blue-3/solve.py

[4] ImaginaryCTF, “Sleepy Alarm — Challenge description and solution,” README, repository ImaginaryCTF-2024-Challenges, commit 21ea0e040638b953f5cc0efca1d900024899a7bc. https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/tree/main/Forensics/Sleepy%20Alarm

[5] ImaginaryCTF, “createsignal.m,” MATLAB generator for Sleepy Alarm, cùng commit 21ea0e040638b953f5cc0efca1d900024899a7bc. https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/blob/main/Forensics/Sleepy%20Alarm/src/createsignal.m

[6] NumPy Developers, “Discrete Fourier Transform (numpy.fft).” https://numpy.org/doc/stable/reference/routines.fft.html

[7] SciPy Developers, “Short-Time Fourier Transform.” https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html

[8] Pillow Developers, “Image class and pixel access.” https://pillow.readthedocs.io/

[9] CTFtime Team, “All about CTF (Capture The Flag),” tài liệu được assignment UET.CN3124 khuyến nghị.

[10] Trường Đại học Công nghệ, ĐHQGHN, “Mô tả bài tập lớn / đồ án thực hành — UET.CN3124: Dự án thực hành CTF Jeopardy,” tài liệu hướng dẫn học phần, đặc biệt các mục 3–7, trang 3–8.

[11] Zeecka, “Aperi'Solve — Steganalysis web platform,” README, repository AperiSolve. https://github.com/Zeecka/AperiSolve (accessed 14 November 2026).

[12] Paweł Kaczmarek and Zbigniew Piotrowski, “The A-Files — Research toolkit for evaluating audio steganography and watermarking,” README, repository The-A-Files. https://github.com/pawel-kaczmarek/The-A-Files (accessed 14 November 2026).

[13] ragibson, “Steganography — Least Significant Bit Steganography for bitmap images, WAV sound files, and byte sequences,” repository README. https://github.com/ragibson/Steganography (accessed 14 November 2026).

## Phụ lục A — Lệnh tái hiện

~~~bash
# Environment and artifacts
uv venv --python 3.14
source .venv/bin/activate
uv pip install -r requirements.txt
python scripts/check_environment.py
python scripts/download_artifacts.py all

# Regression tests
python -m unittest discover -s tests -v

# Blue 3
python src/blue3/analyze.py data/blue3/blue.png
python src/solve_challenges.py blue3 data/blue3/blue.png
python src/blue3/visualize.py data/blue3/blue.png --length 50
python src/experiments/blue3_robustness.py data/blue3/blue.png

# Sleepy Alarm analysis and exact extraction
python src/sleepy_alarm/analyze.py data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
python src/solve_challenges.py sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'

# Paired and asymmetric robustness
python src/experiments/sleepy_alarm_robustness.py data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
python src/experiments/sleepy_alarm_asymmetric_robustness.py data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'

# Steganalysis and expanded robustness scripts (regenerate only after changing code or inputs)
python -m unittest discover -s tests -v
python src/experiments/steganalysis_benchmark.py
python src/experiments/blue3_extended_robustness.py data/blue3/blue.png
python src/experiments/sleepy_alarm_robustness_matrix.py data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
~~~

## Phụ lục B — Checklist hoàn thiện trước khi nộp

Các hạng mục kỹ thuật sau đã có bằng chứng trong repository; trước khi nộp chỉ cần xác nhận bản build cuối cùng không bị thay đổi:
- [ ] Điền họ tên, MSSV, lớp, ngày nộp và hạn nộp trên trang đầu và metadata.
- [x] Quality gate đã ghi nhận 22/22 tests pass, ba artifact khớp hash và hai decoder exact-match (Sleepy Alarm dùng reference); quality-gate JSON/log đã được commit.
- [x] Hai ma trận robustness mới đã chạy, có JSON/CSV và partial-recovery metrics; cập nhật diễn giải trong mục 8.5 và 11.7.6.
- [ ] Hoàn thiện logbook bằng giờ làm thực tế và rà soát phản tư cá nhân tại mục 11.5; không ước lượng thời lượng.
- [ ] Mở PDF cuối và kiểm tra từng trang ở mức phóng đại đọc được: không mất chữ, không cắt hình, bảng không tràn lề, công thức hiển thị đúng.
- [ ] Xác nhận phần nội dung chính không vượt 15 trang; phụ lục và tài liệu tham khảo nằm ngoài phạm vi đếm theo assignment.
- [ ] Mở ZIP cuối, kiểm tra có `data/`, `src/`, `tests/`, `scripts/`, `references/`, `report/` và `results/`; không có `.venv`, cache hoặc secrets.
- [ ] Đối chiếu PDF/ZIP được tạo từ cùng một revision của `main`; không nộp các binary cũ hơn source.


