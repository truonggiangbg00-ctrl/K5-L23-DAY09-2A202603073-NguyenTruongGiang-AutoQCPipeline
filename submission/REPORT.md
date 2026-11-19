# Báo cáo Day 09 — Nguyễn Trường Giang, 2A202603073

## 1. Kết quả tổng quan
Trong bài lab này, em trình bày quy trình kiểm soát chất lượng dữ liệu ảnh và so sánh kết quả huấn luyện trên dữ liệu raw và clean. Kết quả pipeline là **Hold**, chưa đủ điều kiện phát hành dataset. Lô đầu vào gồm 224 ảnh raw, loại 19/224 ảnh ở intake; xuất **205 ảnh dưới dạng bản nháp**. Sau máy sửa và người duyệt mô phỏng 80/125 ảnh trong hàng đợi, còn **0 lỗi bắt buộc**, nhưng **38/205 ảnh (18,54%)** còn cảnh báo chưa duyệt, vượt ngưỡng 10%. Nguồn: `reports/01_intake.csv`, `08_summary.json`, `export/clean_v1/manifest.json`.

## 2. Lỗi và phân việc
Bảng lấy từ `02_error_list_v1.csv`: 208 bản ghi, gồm 19 lỗi intake và 189 bản ghi QC trên 205 ảnh được nhận. Cột số lượng là **số bản ghi / số ảnh khác nhau**; các mã có thể trùng ảnh nên không cộng số ảnh giữa các hàng. Lỗi intake dùng mẫu số 224 ảnh; các mã QC dùng 205 ảnh; lỗi tên lớp/thống kê thuộc cấp dataset.

| Mã | Bản ghi / ảnh | Ai xử lý |
|---|---:|---|
| `BAD_CLASS_ID` | 6 / 6 | Máy |
| `BAD_CLASS_NAME` | 2 / cấp dataset | Máy |
| `BAD_FORMAT` | 3 / 3 | Máy |
| `BAD_SIZE` | 3 / 3 | Máy |
| `BOX_HUGE` | 3 / 3 | Người |
| `BOX_OUT_OF_IMAGE` | 8 / 8 | Máy |
| `BOX_TINY` | 6 / 4 | Người |
| `BOX_ZERO` | 4 / 4 | Máy |
| `CLASS_RARE` | 4 / cấp dataset | Người |
| `CORRUPT_IMAGE` | 2 / 2 | Máy |
| `DUP_BOX` | 7 / 7 | Máy |
| `DUP_IMAGE_EXACT` | 8 / 8 | Máy |
| `DUP_IMAGE_NEAR` | 2 / 2 | Máy |
| `EMPTY_LABEL` | 12 / 12 | Người |
| `LEAK_TEST` | 4 / 4 | Máy |
| `MISSING_LABEL_FILE` | 6 / 6 | Người |
| `POSSIBLE_FALSE_POS` | 29 / 27 | Người |
| `POSSIBLE_LOOSE_BOX` | 28 / 24 | Người |
| `POSSIBLE_MISSING` | 53 / 52 | Người |
| `POSSIBLE_WRONG_CLASS` | 18 / 18 | Người |

Máy loại ảnh theo quy tắc, xóa dòng sai/lặp và cắt box tràn; người quyết định nội dung ngữ nghĩa và gán ảnh thiếu nhãn. `03_fixes.csv` có 35 mục: 20 xóa dòng, 8 cắt box, 1 sửa tên lớp và 6 chuyển người gán; 6 mục cuối **không phải nhãn máy tự tạo**. Hàng đợi đứng đầu là `img_0020` (11,524 điểm: sai lớp + thiếu nhãn + đã xóa dòng), rồi 6 ảnh `NEEDS_LABEL` (10 điểm/ảnh). Trong 80 ảnh đã duyệt có 74 ảnh với 94 cảnh báo ngữ nghĩa từ v2; đây là số cảnh báo được xem, không phải số lỗi thật được xác nhận. 71 cảnh báo vẫn hiện ở v3, nhưng gate chỉ tính ảnh chưa duyệt.

## 3. Calibration (2 ngưỡng)
Nguồn: `calibration/calibration.json` và `calibration_report.md`, sinh bằng hai sweep; chỉ thay hai khóa cho phép.

| Tham số | Trước → sau | Precision / Recall trước → sau | Lý do |
|---|---|---|---|
| `phash_dist` | 2 → **4** | NEAR: 1,000 / 0,500 → 1,000 / 0,667 | Ngưỡng nhỏ nhất tăng recall; tránh loại nhầm ảnh tốt. EXACT vẫn 1/1. |
| `second_opinion.conf` | 0,25 → **0,6** | WRONG_CLASS: 0,556 / 0,833 → 0,625 / 0,833; MISSING: 0,500 / 1,000 → 0,571 / 1,000 | Giảm FP lần lượt 4→3 và 8→6, giữ recall hai nhóm ưu tiên. |

Đánh đổi: LOOSE_BOX giảm P/R từ 0,286/0,400 xuống 0,200/0,200 (chỉ bắt 1/5 lỗi chèn). FALSE_POS giữ 0,312/1,000 vì dùng `fp_conf` riêng. Không tăng conf chỉ để ép Release.

**Calib có thể đánh lừa:** ở pHash 16, calib cho NEAR P=1 và R=0,833; kiểm ảnh raw cho thấy `img_0011` (tennis) bị gộp với `img_0008` (trượt tuyết), khoảng cách 16. Vì vậy không chọn ngưỡng có F1 cao nhất một cách máy móc. Bằng chứng hình: `evidence/duplicate_pairs.jpg`. Ở ngưỡng chọn 4, raw có 8 trùng byte, 2 gần trùng, 4 rò rỉ test/val; không có đáp án toàn bộ raw nên không tuyên bố precision raw bằng 100%.

## 4. Kiểm tra gate và các hạn chế
Thí nghiệm: `python -m pipeline.run --budget 0 --work work/run_nb --reports submission/evidence/no_review --export-dir work/exp_nb` cho **Rework, mã 20**, còn 6 `MISSING_LABEL_FILE`; không có `work/exp_nb/clean_v1/manifest.json`. Báo cáo được giữ riêng trong `evidence/no_review/`.

Điểm mù có bằng chứng: (1) pHash 4 bỏ sót cặp biến đổi `img_0077`/`img_0223` (khoảng cách 6) và `img_0074`/`img_0084` (16), quan sát cùng cảnh; (2) checker bỏ sót 4/5 lỗi box lỏng và 1/6 lỗi sai lớp chèn trong calib. Release, nếu có, chỉ là đạt quy tắc gate, không bảo đảm nhãn đúng hoàn toàn.

Quan sát ảnh raw: `img_0001` thiếu box quanh người đứng bên phải ở giữa ảnh (đồng thời check báo box lặp dòng 3); `img_0042`/`img_0076` cùng cảnh xe buýt; `img_0077`/`img_0223` cùng cảnh với biến đổi hình. Hình tổng hợp 10 ảnh đã xem: `evidence/labels_contact.jpg`.

## 5. So sánh huấn luyện trên dữ liệu raw và clean
Đã chạy đủ **4 lượt, 20 epoch/lượt**, YOLO26n, ảnh 640 px, batch 4, seed 0 và 1 cho mỗi biến thể, trên RTX 3050 4 GB. Giữ cùng trọng số ban đầu, siêu tham số, gold_val 40 ảnh để chọn checkpoint và test 100 ảnh để đánh giá cuối. Kết quả do `scripts/train_compare.py` sinh; bảng dưới do `scripts/summarize_results.py` sinh.

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.623 ± 0.087 | 0.433 ± 0.046 | 0.682 ± 0.051 | 0.553 ± 0.121 |
| clean | 205 | 2 | 0.680 ± 0.016 | 0.487 ± 0.006 | 0.811 ± 0.031 | 0.551 ± 0.030 |

Chênh mAP50 (clean − raw) = **+0.057**.

Số ảnh trong bảng là ảnh đã copy theo script. Loader thực tế dùng **213/224 raw** (bỏ 11 ảnh/nhãn hỏng) và **205/205 clean**. Bằng chứng: `evidence/raw_loader_audit.json`, `clean_loader_audit.json`. Không sửa dữ liệu gốc hay JSON kết quả để thay đổi số này.

mAP50 theo seed: raw 0,5616 / 0,6844; clean 0,6684 / 0,6909. Chênh cùng seed lần lượt +0,1068 và +0,0065. Trung bình clean cao hơn khoảng 0,0567, nhưng thấp hơn độ lệch chuẩn raw khoảng 0,0868; chỉ hai seed và test nhỏ nên **chưa đủ bằng chứng để khẳng định mức cải thiện ổn định**. mAP50–95 tăng khoảng 0,0539 và precision tăng khoảng 0,1289; recall gần như không tăng (clean 0,551 so với raw 0,553). Không kết luận mọi mặt đều tốt hơn.

Hai giả thuyết và cách kiểm: (1) sửa nhãn và duyệt 80 ảnh giúp giảm box thừa/sai lớp, tăng precision; kiểm bằng thí nghiệm ablation auto-only so với clean trên cùng tập ảnh và thêm seed. (2) raw chứa ảnh trùng/rò rỉ test/val (intake đã phát hiện 4 ảnh), còn loader tự bỏ 11 ảnh hỏng, nên chênh lệch còn do thành phần tập train; kiểm bằng các nhóm có cùng danh sách ảnh sau xử lý rò rỉ, cùng siêu tham số, và một tập test độc lập đã khóa. Chưa thực hiện hai thí nghiệm bổ sung này. Việc tiếp theo: thêm seed và duyệt cảnh báo còn lại; giữ dataset hiện tại ở trạng thái Hold.

Tái lập: `evidence/training_protocol.json` chứa lệnh, phiên bản và checksum; `evidence/training_logs/` chứa đủ 20 epoch của từng lượt. Hai lượt clean cuối được chạy lại sau khi chuẩn hóa xuống dòng manifest về LF (nội dung JSON không đổi), để checksum byte của script train khớp checker gốc. Dấu vân tay cấu hình, manifest và script của bốn kết quả cuối được lưu trong protocol. Trọng số `best.pt` giữ trong `work/train/runs/`, không commit lên Git.

## 6. Kết luận và cách sử dụng AI trong bài làm
Giữ **Hold** và bản nháp 205 ảnh. Để đạt ngưỡng với mẫu số này cần dưới 21 ảnh chưa xử lý, tức ít nhất 18 trong 38 ảnh cảnh báo hiện tại phải được giải quyết, không phát sinh lỗi mới. Ngân sách 80 cố định trong lab: không tự tăng ngân sách, đổi ngưỡng gate hay sửa báo cáo để đạt Release; công việc còn lại cần vòng duyệt được dự án cho phép.

### Vai trò của người học và công cụ AI

Em thực hiện bài lab với sự hỗ trợ của Codex trong quá trình học và triển khai. Em xác định phạm vi công việc, yêu cầu hoàn thiện phần lõi trước rồi bổ sung phần so sánh huấn luyện raw–clean. Báo cáo trình bày kết quả bài làm của em dựa trên các sản phẩm được lưu trong repository.

AI được sử dụng để hướng dẫn cách tiếp cận bài, giải thích các bước của pipeline và hỗ trợ coding: gợi ý cách xử lý, viết và chỉnh sửa các module, giải thích lỗi và hỗ trợ xử lý môi trường Windows. AI cũng hỗ trợ chạy các lệnh kiểm tra, huấn luyện theo yêu cầu và tổng hợp số liệu từ CSV, JSON và log thành bảng so sánh, nhận xét và bản thảo báo cáo. Phần mã nguồn và nội dung báo cáo vì vậy có sự hỗ trợ trực tiếp của AI.

Các nhận xét trong báo cáo có dẫn nguồn kết quả để kiểm tra lại. Với vai trò người nộp bài, em chịu trách nhiệm về nội dung báo cáo và việc giải thích mã nguồn khi được hỏi. Việc đọc lại code và đối chiếu bằng chứng là bước cần hoàn thành trước khi nộp. Trong phạm vi lab, bước duyệt 80 ảnh được thực hiện bằng cơ chế mô phỏng của đề.

Ví dụ yêu cầu dành cho AI: hướng dẫn hoàn thiện 4 module còn thiếu theo docstring và test, hỗ trợ giải thích lỗi khi chạy, tổng hợp kết quả raw–clean từ các file đầu ra; giữ nguyên dữ liệu gốc, file mẫu và cấu hình cố định. Một vấn đề môi trường đã gặp là UnicodeDecodeError khi cài thư viện trên Windows; cách xử lý là dùng `-X utf8`/`PYTHONUTF8=1`.

Ghi chú tái lập Windows: checker gốc báo nhầm 2 lỗi ở chính `pipeline/calibrate.py` do so đường dẫn `\` với danh sách `/`. Trình chạy `scripts/check_submission_windows.py` chỉ chuẩn hóa phép so đường dẫn; giữ nguyên file đề và toàn bộ kiểm tra hash/test/cấu hình. Ba ca bổ sung (6 assert) ở `evidence/edge_cases.py` đã đạt.

Kiểm tra cuối: `python -X utf8 scripts/check_submission_windows.py` đạt **79/79 test, 0 lỗi, 0 cảnh báo**, gồm cả train và checksum; log ở `evidence/final_validation.txt`.
