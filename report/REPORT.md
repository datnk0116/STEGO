# Báo cáo đồ án thực hành CTF Jeopardy
## UET.CN3124 — An toàn và an ninh mạng

**Tên đề tài:** Phân tích kỹ thuật ẩn tin trong ảnh và âm thanh: nghiên cứu Blue 3 và Sleepy Alarm  
**Sinh viên:** [HỌ VÀ TÊN] — **MSSV:** [MSSV]  
**Lớp:** [LỚP] — **Ngày nộp:** [NGÀY NỘP]

> **Trạng thái:** Bản thảo nghiên cứu có thể tái lập. Các trường [CẦN THỰC NGHIỆM] phải được thay bằng kết quả do sinh viên trực tiếp chạy. Không được tự điền flag, runtime, metric hoặc kết quả chưa đo.

## Tóm tắt

Báo cáo nghiên cứu hai challenge CTF thuộc chủ đề Steganography: Blue 3 (BYUCTF) và Sleepy Alarm (ImaginaryCTF 2024). Mục tiêu là khảo sát cách dữ liệu có thể được nhúng trong ảnh thông qua biến đổi pixel và trong âm thanh thông qua cấu trúc tín hiệu; xây dựng quy trình phân tích độc lập; đánh giá khả năng tái hiện; và thảo luận dấu hiệu phát hiện dưới góc nhìn phòng thủ.

Phương pháp gồm: (1) thu thập và xác minh artifact chính thức; (2) khảo sát metadata, định dạng và đặc trưng tín hiệu; (3) kiểm tra giả thuyết bằng script; (4) đối chiếu kết quả và ghi nhận giới hạn. Với ảnh, quy trình tập trung vào histogram, kênh màu và sai khác pixel. Với âm thanh, quy trình khảo sát waveform, phổ Fourier và spectrogram. Kết quả thực nghiệm sẽ chỉ được báo cáo sau khi chạy trên artifact gốc.

**Kết quả thực nghiệm:** [CẦN THỰC NGHIỆM — ghi phát hiện, SHA-256, số liệu và ảnh minh chứng thực tế.]

**Từ khóa:** Capture The Flag, steganography, steganalysis, pixel analysis, audio signal processing, FFT, spectrogram.

## 1. Giới thiệu và mục tiêu

### 1.1. Bối cảnh

Steganography là kỹ thuật che giấu sự tồn tại của thông điệp trong một vật mang tin (cover object), khác với cryptography vốn tập trung biến đổi nội dung bằng mật mã. Trong bài toán CTF, người giải được cung cấp file và cần suy luận cách dữ liệu được nhúng, sau đó khôi phục thông điệp.

Ảnh số và âm thanh số là hai vật mang tin phù hợp để nghiên cứu vì chúng chứa nhiều mẫu số. Thay đổi nhỏ trong các mẫu có thể khó nhận biết bằng quan sát thông thường nhưng có thể bộc lộ qua phân tích thống kê hoặc tín hiệu.

### 1.2. Mục tiêu

1. Thiết lập môi trường phân tích offline có thể tái lập.
2. Phân tích hai challenge chung chủ đề Steganography nhưng khác loại vật mang tin.
3. Tự triển khai công cụ kiểm tra thay vì chỉ chạy công cụ đóng gói.
4. Ghi lại giả thuyết, lệnh, đầu ra, lỗi và cách khắc phục.
5. Đánh giá điều kiện thành công, giới hạn, dấu hiệu phát hiện và biện pháp phòng thủ.
6. So sánh hai loại vật mang tin và đề xuất mở rộng có thể kiểm chứng.

### 1.3. Phạm vi và câu hỏi nghiên cứu

- RQ1: Đặc trưng nào của ảnh giúp nhận diện khả năng dữ liệu đã được nhúng bằng biến đổi pixel?
- RQ2: Phân tích miền thời gian, miền tần số và spectrogram hỗ trợ phát hiện cấu trúc ẩn trong âm thanh như thế nào?
- RQ3: Kết quả có tái lập được khi sử dụng cùng artifact, môi trường và lệnh?
- RQ4: Những thao tác xử lý ảnh/âm thanh nào có thể phá hủy hoặc làm suy giảm thông tin steganographic?

Phạm vi chỉ bao gồm file challenge công khai và bản sao cục bộ. Không thực hiện tấn công hoặc thu thập dữ liệu trên hệ thống ngoài phạm vi cho phép.

## 2. Bối cảnh challenge và kiến thức nền

### 2.1. Blue 3 — BYUCTF

Blue 3 được BYU-CSA mô tả ở mức Hard. Flag được tách thành từng ký tự; với ký tự thứ i, bộ tạo chọn ngẫu nhiên ord(c) lần, mỗi lần tăng 1 một kênh màu ngẫu nhiên của một pixel trong vùng vuông thứ i trên đường chéo. Ảnh nền là RGB (64, 77, 205), kích thước 512×512. Các vùng có kích thước floor(512/L) × floor(512/L), trong đó L là độ dài flag; phần dư ở mép phải/dưới không thuộc các vùng được duyệt. Solver upstream ước lượng màu nền phổ biến nhất, thử độ dài L, cộng tổng chênh lệch ba kênh so với màu nền trong từng vùng rồi ánh xạ tổng sang mã ký tự. Bản triển khai độc lập nằm tại `src/solve_challenges.py`. Challenge hard-mode chỉ phân phối blue.png; create.py/solve.py là tài liệu tham khảo của tác giả, không phải artifact bắt buộc cho người chơi.

Artifact cần thu thập: ảnh gốc và file mô tả/source từ kho BYU được liệt kê trong `data/README.md`.

Câu hỏi phân tích: dữ liệu có được biểu diễn bằng sự khác biệt giữa pixel hoặc giữa các vùng ảnh hay không; thứ tự duyệt pixel/vùng, kênh màu, ngưỡng và ánh xạ ký tự được xác định như thế nào? Không khẳng định thuật toán cụ thể trước khi đối chiếu source và dữ liệu.

### 2.2. Sleepy Alarm — ImaginaryCTF 2024

Sleepy Alarm thuộc category Forensics, độ khó Medium, tác giả Minerva. Challenge cung cấp `togive/morning_n_breakfast.mp3` và gợi ý độ dài flag là 39 ký tự (tính cả ictf và dấu ngoặc nhọn). Writeup chính thức mô tả một thành phần jingle yếu với peak bất thường ở 8 kHz. Sau khi cô lập sóng mang 8 kHz, tín hiệu có ba mức biên độ: 2×10⁻³ biểu diễn bit 0, 5×10⁻³ biểu diễn bit 1 và 0 biểu diễn điểm kết thúc byte. Mỗi bit kéo dài 0,02 giây, tương ứng 50 baud. Đây là Amplitude Shift Keying (ASK). Challenge repository còn công bố file gốc `morning_n_breakfast_original.mp3` và script MATLAB tạo tín hiệu; có thể dùng cặp original/challenge để so sánh, nhưng lời giải phải được tái hiện trên file phân phối cho người chơi.

Artifact cần thu thập: file âm thanh phát hành chính thức trong challenge repository của ImaginaryCTF 2024, cùng mô tả challenge và writeup tham khảo (nếu có).

Câu hỏi phân tích: tín hiệu có thành phần tần số, khoảng thời gian, kênh stereo hoặc mẫu lặp bất thường hay không; spectrogram/FFT có làm lộ cấu trúc không quan sát rõ khi nghe thông thường hay không? Không mặc định thông điệp được mã hóa bằng một tần số cố định.

### 2.3. Kiến thức nền

#### 2.3.1. Mô hình nhúng

Mô hình tổng quát: `stego = Embed(cover, message, key, parameters)`. Quá trình trích xuất: `message′ = Extract(stego, key, parameters)`. Ba thuộc tính cần xem xét là tính bí mật (khó nhận biết), dung lượng và độ bền trước biến đổi vật mang tin.

#### 2.3.2. Ảnh số

Ảnh raster biểu diễn thành ma trận mẫu. Với RGB, mỗi pixel có ba thành phần R, G, B. Có thể khảo sát kích thước, mode, bit depth, metadata, histogram từng kênh, phân bố giá trị và sai khác pixel. Với Blue 3, base image theo creator source là màu đồng nhất RGB (64,77,205), vì vậy có thể dùng chính màu này làm baseline thay vì cần một file cover riêng. Với hai ảnh A và B cùng kích thước: `D(x,y,c) = |A(x,y,c) − B(x,y,c)|`. Thống kê D gồm tỷ lệ pixel khác 0, trung bình, cực đại và histogram.

#### 2.3.3. Âm thanh số

Âm thanh rời rạc được biểu diễn bởi `x[n]`, với tần số lấy mẫu `f_s`. Thời lượng lý thuyết là `N/f_s` giây cho N mẫu. Phân tích miền thời gian khảo sát biên độ, khoảng lặng, clipping và tuần hoàn.

Biến đổi Fourier rời rạc:

`X[k] = Σ(n=0..N−1) x[n] exp(−j 2πkn/N)`

Độ phân giải tần số của FFT N điểm là `f_s/N`. Spectrogram biểu diễn năng lượng theo thời gian và tần số; STFT chia tín hiệu thành các khung, nhân cửa sổ rồi thực hiện Fourier. Cần ghi rõ FFT size, loại cửa sổ và hop length vì chúng ảnh hưởng độ phân giải.

#### 2.3.4. Steganalysis và giới hạn

Steganalysis tìm dấu hiệu thống kê hoặc cấu trúc bất thường. Không có một dấu hiệu đơn lẻ nào chứng minh chắc chắn tồn tại dữ liệu ẩn. Hậu kỳ ảnh, codec, nén, resampling và filtering đều có thể tạo bất thường tương tự. Kết luận phải kết hợp nhiều bằng chứng và nêu false positives.

## 3. Môi trường thực nghiệm

### 3.1. Cấu hình

- Hệ điều hành: macOS 15.7.4
- Kiến trúc CPU: arm64
- Python: 3.14.10
- Pillow 13.0.0; NumPy 2.5.4; SciPy 1.18.1; Matplotlib 3.11.2; SoundFile 0.14.0 (theo log môi trường ngày 14-11-2026).
- Môi trường: virtual environment `.venv`.
- Dữ liệu: bản sao artifact upstream, không chỉnh sửa bản gốc.

### 3.2. Công cụ

- Python: tự động hóa kiểm tra và phân tích.
- Pillow: đọc ảnh và khảo sát pixel.
- NumPy: tính toán mảng và FFT.
- SciPy và SoundFile: đọc/đặc trưng âm thanh.
- Matplotlib: biểu diễn waveform, phổ và spectrogram.
- ExifTool, `file`, `shasum`: kiểm tra metadata, định dạng và tính toàn vẹn.

### 3.3. Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate      # Windows
python -m pip install -r requirements.txt
python scripts/check_environment.py
```

### 3.4. Tính toàn vẹn

Mỗi artifact được giữ nguyên và có SHA-256 ghi trong `results/artifact_manifest.txt`. Không chạy công cụ biến đổi trực tiếp trên file gốc. Mọi file chuyển đổi, lọc hoặc resample phải được lưu riêng và ghi tham số.

## 4. Quy trình thực hiện

### 4.1. Quy trình chung

1. Đọc mô tả challenge và ghi nguồn tải/ngày truy cập.
2. Tải artifact từ kho phát hành chính thức.
3. Xác minh file, định dạng, kích thước và SHA-256.
4. Phân tích sơ bộ bằng công cụ hệ thống và script.
5. Nêu giả thuyết có thể kiểm chứng; mỗi giả thuyết phải có phép thử và kết quả.
6. Triển khai hoặc điều chỉnh script độc lập.
7. Đối chiếu với source/writeup upstream và trích dẫn rõ ràng.
8. Chạy lại từ môi trường sạch.
9. Lưu log, ảnh chụp terminal và kết quả trung gian.

### 4.2. Blue 3 — phân tích ảnh

**Bước 1 — Kiểm tra file:** ghi kích thước, mode, định dạng, metadata và SHA-256.

**Bước 2 — Khảo sát pixel:** xuất histogram kênh màu và thống kê cơ bản; kiểm tra màu RGB (64,77,205), tỷ lệ pixel đúng màu nền và phân bố tổng sai khác có dấu.

**Bước 3 — Hình thành giả thuyết:** source creator cho biết mỗi ký tự c được biểu diễn bởi tổng số lần tăng kênh màu bằng `ord(c)` trong vùng đường chéo tương ứng. Vì mỗi thay đổi chỉ tăng một đơn vị ở một kênh, tổng sai khác RGB trong một vùng phải khôi phục được mã ký tự, miễn là màu nền và phân vùng được xác định đúng. Cụ thể, với L ký tự và ảnh 512×512, mỗi vùng có cạnh `floor(512/L)`; vùng i có góc trên-trái `(i·w, i·h)`.

**Bước 4 — Kiểm thử:** solver upstream ước lượng màu nền từ màu phổ biến nhất. Bản tái triển khai sử dụng baseline đã biết từ creator source RGB (64,77,205), sau đó thử các ứng viên L. Với từng i, cộng `R−64 + G−77 + B−205` trong vùng vuông đường chéo để thu mã ký tự. Dừng khi chuỗi khớp regex `byuctf{[0-9A-Za-z_]*}`. Script độc lập: `python src/solve_challenges.py blue3 data/blue3/blue.png`. Việc biết baseline từ source được ghi nhận là lợi thế white-box; cần thêm phép thử suy luận baseline từ ảnh để đánh giá tình huống black-box.

**Bước 5 — Xác minh:** kết quả cần có định dạng hợp lý và được đối chiếu độc lập với logic tạo challenge. Không dùng flag trong source làm bằng chứng duy nhất cho khả năng giải từ artifact.

Bằng chứng cần có: ảnh đầu vào và SHA-256; metadata; histogram; log script; đầu ra trung gian; phép kiểm tra kết quả; ảnh chụp terminal.

### 4.3. Sleepy Alarm — phân tích âm thanh

**Bước 1 — Kiểm tra container/codec:** ghi sample rate, số kênh, số frame, sample width, thời lượng và SHA-256.

**Bước 2 — Nghe và quan sát:** nghe ở mức âm lượng an toàn; ghi đoạn bất thường nhưng không kết luận chỉ dựa vào thính giác.

**Bước 3 — Waveform:** vẽ biên độ theo thời gian; kiểm tra khoảng lặng, clipping, đoạn lặp và thay đổi năng lượng.

**Bước 4 — FFT/STFT:** source mô tả sóng mang 8 kHz và 50 baud (0,02 s/bit). Dùng band-pass quanh 8 kHz, tính analytic signal/envelope bằng Hilbert transform, lấy trung vị biên độ ở phần giữa mỗi symbol để tránh chuyển tiếp. Phân loại gần 0,002 thành 0, gần 0,005 thành 1, mức gần 0 thành dấu phân cách byte. Script độc lập: `python src/solve_challenges.py sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3`. Tham số lọc và ngưỡng là lựa chọn triển khai cần đánh giá độ nhạy, không phải một phần được nguyên văn xác định đầy đủ trong mô tả challenge.

**Bước 5 — Kiểm thử giả thuyết:** challenge được phân phối là bản alarm đã trộn tín hiệu ASK với nhạc nền; repository upstream có bản original tương ứng. Bản triển khai đồng bộ reference bằng resampling khi cần, ước lượng độ lệch mẫu qua cross-correlation rồi chỉ so sánh phần overlap. Phải lưu lag, overlap duration và normalized correlation. Nếu không dùng reference, lọc quanh sóng mang và kiểm tra envelope. Mọi xử lý tạo file mới và ghi tham số.

**Bước 6 — Xác minh:** giải mã ASK theo khung 0,02 giây/symbol, đọc 8 bit thành một byte và xem mức 0 là dấu phân cách/hoàn tất byte theo source. Dùng gợi ý độ dài flag 39 ký tự để kiểm tra tính đầy đủ, không dùng hint làm bằng chứng duy nhất. Đối chiếu chuỗi với cơ chế tạo trong `createsignal.m`.

Bằng chứng cần có: metadata âm thanh; waveform; spectrogram có trục thời gian/tần số; cấu hình FFT/STFT; log; đầu ra trung gian; kết quả xác minh.

## 5. Kết quả thực nghiệm

> Hoàn thiện phần này sau khi trực tiếp chạy challenge artifacts. Không thay thế trường chưa đo bằng số liệu ước lượng.

### 5.1. Blue 3

- Upstream image: `blue.png`, 9,406 bytes; Git blob `1dc26a1dde421a6ed0a553c89256e0ad75394c6b`.
- Upstream challenge source explains the diagonal-region character encoding; the independent decoder is in `src/solve_challenges.py`.
- Artifact filename: `data/blue3/blue.png`.
- Kích thước: 9,406 bytes; PNG, RGB, 512×512; 262,144 pixel; Pillow báo không có metadata keys.
- SHA-256 local: `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e`.
- R channel: min=64, max=68, mean=64.00663375854492, std=0.09345379422886371, 5 unique values.
- G channel: min=77, max=81, mean=77.00653076171875, std=0.09425359809012815, 5 unique values.
- B channel: min=205, max=209, mean=205.00653457641602, std=0.09423309511716214, 5 unique values.
- Giả thuyết đã xác nhận theo solver: màu nền RGB (64,77,205); tổng sai khác RGB trong từng vùng vuông đường chéo cho mã ký tự.
- Lệnh: `python src/blue3/analyze.py data/blue3/blue.png` và `python src/solve_challenges.py blue3 data/blue3/blue.png`.
- Kết quả terminal: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}`; solver thử 49 candidate lengths và báo `Format validated: True`.
- Thời gian chạy: chưa được đo/ghi lại.

**Diễn giải:** [Giải thích dựa trên log và dữ liệu thực tế; phân biệt suy luận, quan sát và xác minh.]

### 5.2. Sleepy Alarm

- Official distributed audio: `morning_n_breakfast.mp3`, 179,283 bytes; Git blob `5140f9652af9848374263dca3fdfcd9469903c4d`.
- Official description specifies an 8 kHz ASK carrier, 50 baud, amplitude levels 0.002 (bit 0), 0.005 (bit 1), and zero as byte separator; official source also contains an original audio track and MATLAB signal-generation script.
- Artifact filename: `data/sleepy_alarm/morning_n_breakfast.mp3`; reference: `data/sleepy_alarm/morning_n_breakfast_original.mp3`.
- Distributed MP3: 179,283 bytes; local SHA-256 `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2`.
- Original MP3: 160,495 bytes; local SHA-256 `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad2`.
- Initial analyzer run failed because it required identical sample rate/frame/channel dimensions. The updated analyzer now resamples and aligns by cross-correlation; successful run and alignment metrics are still pending.
- Codec/container: [CẦN THỰC NGHIỆM — re-run analyzer after alignment update].
- Sample rate / channels / frame count: [CẦN THỰC NGHIỆM]
- Thời lượng: [CẦN THỰC NGHIỆM]
- Sóng mang/baud/chu kỳ bit theo mô tả chính thức: 8.000 Hz / 50 baud / 0,02 s mỗi bit.
- Quan sát waveform: [CẦN THỰC NGHIỆM]
- Quan sát spectrogram: [CẦN THỰC NGHIỆM]
- Kết quả trích xuất đã xác minh: [CẦN THỰC NGHIỆM]
- Thời gian chạy: [CẦN THỰC NGHIỆM]

**Diễn giải:** [Giải thích vì sao cấu trúc phát hiện tương ứng kết quả, tham số quan trọng và cách loại trừ giải thích thay thế.]

### 5.3. Tổng hợp

| Khía cạnh | Blue 3 (ảnh) | Sleepy Alarm (âm thanh) |
|---|---|---|
| Vật mang tin | Raster image | Digital audio |
| Miền phân tích | Không gian/pixel/kênh màu | Thời gian/tần số/kênh |
| Công cụ chính | Pillow, NumPy | SciPy, NumPy, Matplotlib |
| Dấu hiệu quan sát | [điền] | [điền] |
| Tham số nhạy cảm | [điền] | [điền] |
| Kết quả xác minh | [điền] | [điền] |
| Giới hạn | [điền] | [điền] |

## 6. Phân tích kỹ thuật và phòng thủ

### 6.1. Góc nhìn tấn công

Ẩn tin thành công khi người quan sát không nhận ra vật mang tin chứa dữ liệu bổ sung và quy trình trích xuất biết cách diễn giải mẫu đã nhúng. Trong CTF, người giải thường biết phạm vi và có mô tả challenge; trong thực tế, người phân tích có thể không có cover gốc, key hoặc thông tin thuật toán.

Với Blue 3, cách giải dựa vào tổng sai khác tuyệt đối có dấu so với base color, nên thay đổi pixel ngoài cơ chế tạo, clipping ở biên kênh màu hoặc các phép biến đổi làm lệch baseline có thể làm sai tổng mã ký tự; resize/crop đặc biệt có thể phá vỡ phân vùng. Với Sleepy Alarm, lossy compression, resampling, filtering, mixing hoặc normalization có thể làm thay đổi biên độ/pha của sóng mang 8 kHz và gây lỗi phân loại ASK. Độ bền phải được đo bằng thí nghiệm.

### 6.2. Góc nhìn phòng thủ

- Kiểm tra định dạng thực tế và metadata, không tin tuyệt đối phần mở rộng.
- So sánh hash với bản tin cậy nếu có.
- Kết hợp phân tích thống kê và cấu trúc ảnh/audio.
- Phát hiện mẫu phổ hoặc pixel bất thường bằng nhiều đặc trưng.
- Bảo toàn bản gốc trước khi chuyển đổi.
- Ghi nguồn, chuỗi xử lý và hash phục vụ điều tra.

Một cảnh báo steganalysis chỉ là chỉ dấu để điều tra tiếp, không tự động chứng minh hành vi độc hại. Ảnh nghệ thuật, filter, watermark, codec và hậu kỳ đều có thể gây false positives.

### 6.3. Điều kiện thành công và giới hạn

- Phải dùng đúng artifact và bảo toàn dữ liệu.
- Cần xác định đúng định dạng và phương pháp giải mã.
- So sánh ảnh cần cover reference tương thích kích thước, căn chỉnh và mã hóa.
- FFT/STFT phụ thuộc tham số; chọn sai cửa sổ hoặc độ phân giải có thể che khuất đặc trưng.
- Kết quả cần xác minh độc lập, không chỉ dựa vào chuỗi trông giống flag.

## 7. Tùy biến và mở rộng

Các mở rộng được thiết kế trong repository:

1. Image analyzer: đọc ảnh, in metadata, histogram và thống kê kênh.
2. Audio analyzer: đọc file, in đặc trưng tín hiệu, tạo waveform và spectrogram.
3. Integrity manifest: ghi SHA-256 và thông tin artifact để tái lập.
4. Robustness experiment: `src/experiments/robustness.py` tạo các bản sao JPEG quality 95/85/70, resize 0.75/0.5, audio resampling round-trip và gain/clipping. Chạy solver trên từng bản sao và ghi kết quả thành công/thất bại; không diễn giải độ bền khi chưa thực nghiệm.
5. Comparative evaluation: so sánh vật mang tin, độ nhạy tham số, khả năng tự động hóa và false positives.
6. Synthetic regression tests: `tests/test_blue3_solver.py` sinh ảnh giả lập theo creator algorithm để kiểm tra decoder; `tests/test_audio_alignment.py` kiểm tra đồng bộ sample offset, khác sample rate và lệch số kênh. Lệnh chạy: `python -m unittest discover -s tests -v`. Các test mới được thêm, cần chạy và lưu log trước khi báo cáo là đã pass.

**Triển khai trong repository:** `src/solve_challenges.py` chứa hai solver; `src/blue3/analyze.py` và `src/sleepy_alarm/analyze.py` chứa analyzer; `src/audio_alignment.py` đồng bộ reference; `src/experiments/robustness.py` sinh các biến thể có kiểm soát. Regression tests đã được thêm nhưng chưa có log xác nhận chạy pass trong môi trường người dùng. **Kết quả từng mở rộng:** [CẦN THỰC NGHIỆM — ghi commit, lệnh, input hash, output, solver success/failure, số liệu và ảnh minh chứng.]

## 8. Đánh giá, phản biện và tự học

### 8.1. Điểm mạnh
- Hai challenge chung trọng tâm Steganography nhưng khác vật mang tin.
- Kết hợp khảo sát thủ công, phân tích tín hiệu/thống kê và tự động hóa.
- Có thể tái hiện offline trên artifact cục bộ.
- Hash, lệnh, phiên bản công cụ và log hỗ trợ kiểm chứng.

### 8.2. Hạn chế
- Challenge CTF có thể đơn giản hóa giả định so với steganography thực tế.
- Không có cover/reference thì kết luận so sánh pixel bị giới hạn.
- FFT/spectrogram phụ thuộc tham số; hình phổ không tự chứng minh có thông điệp.
- Writeup công khai làm giảm tính độc lập nếu đọc trước khi tự phân tích.
- Hai challenge không đại diện cho toàn bộ thuật toán ẩn tin.

### 8.3. Phản biện phương pháp

Để giảm thiên kiến xác nhận, ghi giả thuyết trước khi thử, lưu cả trường hợp thất bại, xác định điều kiện bác bỏ và đối chiếu với ít nhất một phương pháp độc lập. Khi source challenge công khai, phải đánh dấu chi tiết biết từ source so với chi tiết suy ra từ artifact. Solver khớp source chưa đủ chứng minh phương pháp steganalysis phát hiện payload trong tình huống black-box.

### 8.4. Bài học và hướng học tiếp

Hướng tiếp theo gồm thống kê ảnh nâng cao, steganalysis dựa trên mô hình, audio watermark/steganography, phân tích codec và đánh giá độ bền. Mỗi hướng cần dataset và phép đánh giá rõ ràng.

## 9. Kết luận

Đồ án xây dựng quy trình thực nghiệm thống nhất để nghiên cứu hai challenge Steganography trên ảnh và âm thanh. Giá trị không chỉ là khôi phục thông điệp mà còn giải thích cách dữ liệu được biểu diễn, xác minh bằng chứng cứ, đánh giá điều kiện/giới hạn và phát triển công cụ có thể tái lập. Kết luận cuối cùng về từng challenge chỉ được chốt sau khi artifact chính thức được tải, hash được ghi nhận và quy trình được chạy thành công từ môi trường sạch.

## Tài liệu tham khảo

[1] BYU-CSA, “Blue 3? — challenge description and write-up,” `forensics-steganography/blue-3/README.md`, commit 18c8f246756e79069c1cb1753c8bfea5e73e31f5. https://github.com/BYU-CSA/old-ctf-challenges/tree/master/forensics-steganography/blue-3 (truy cập: 14-11-2026).

[2] ImaginaryCTF, “Sleepy Alarm — challenge description and solution,” `Forensics/Sleepy Alarm/readme.md`, repository ImaginaryCTF-2024-Challenges. https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/tree/main/Forensics/Sleepy%20Alarm (truy cập: 14-11-2026).

[3] BYU-CSA, `create.py` and `solve.py` in the Blue 3 directory, upstream commit 18c8f246756e79069c1cb1753c8bfea5e73e31f5.

[4] ImaginaryCTF, `src/createsignal.m`, `src/morning_n_breakfast_original.mp3`, and `togive/morning_n_breakfast.mp3`, upstream commit 21ea0e040638b953f5cc0efca1d900024899a7bc.

[5] CTFtime team, “All about CTF (Capture The Flag),” tài liệu được assignment UET.CN3124 khuyến nghị.

[6] UET.CN3124, “Mô tả bài tập lớn / đồ án thực hành — Dự án thực hành CTF Jeopardy,” tài liệu học phần, mục 3–8.

[7] NumPy Developers, “Discrete Fourier Transform (numpy.fft),” https://numpy.org/doc/stable/reference/routines.fft.html (truy cập: [ngày truy cập thực tế]).

[8] SciPy Developers, “Short-Time Fourier Transform,” https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html (truy cập: [ngày truy cập thực tế]).

## Phụ lục A — Lệnh tái hiện

```bash
python -m pip install -r requirements.txt
python scripts/check_environment.py
shasum -a 256 data/blue3/blue.png
python src/blue3/analyze.py data/blue3/blue.png
python src/sleepy_alarm/analyze.py data/sleepy_alarm/<official-audio-file>
```

## Phụ lục B — Checklist trước khi nộp

- [ ] Điền họ tên, MSSV, lớp và ngày nộp.
- [ ] Tải artifact từ nguồn chính thức và lưu URL cụ thể.
- [ ] Ghi SHA-256 tất cả artifact.
- [ ] Chạy lại từ môi trường sạch.
- [ ] Lưu ảnh chụp màn hình cài đặt, phân tích, kết quả trung gian và kết quả cuối.
- [ ] Xác minh độc lập với writeup/source tham khảo.
- [ ] Hoàn thành ít nhất một phần mở rộng có kết quả thực nghiệm.
- [ ] Phân tích góc nhìn tấn công và phòng thủ.
- [ ] Điền mọi trường [CẦN THỰC NGHIỆM] và xóa hướng dẫn biên tập.
- [ ] Kiểm tra trích dẫn, chú thích hình, đánh số bảng/hình và xuất PDF.
- [ ] Đảm bảo báo cáo chính không quá 15 trang, không tính phụ lục/tài liệu tham khảo.